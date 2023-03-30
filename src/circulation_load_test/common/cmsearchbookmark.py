import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

import atoma
from atoma.atom import AtomFeed

from circulation_load_test.common.cmbookmarks import (
    CMBookmark,
    CMBookmarkBody,
    CMBookmarkTarget,
    CMLocatorPage,
    CMMotivation,
)
from circulation_load_test.common.cmuser import CMAuthenticationLinkType, CMHTTPUser
from circulation_load_test.common.words import Words


@dataclass
class CMBook:
    borrow_link: str
    book_id: str
    revoke_link: Optional[str]
    annotations_link: Optional[str]


@dataclass
class CMSearchAndBookmarkResults:
    book: Optional[CMBook]
    next_feed: Optional[AtomFeed]


class CMSearchAndBookmark:
    """Search for a book that we can borrow, and read/write bookmarks for it."""

    def __init__(self, search: str):
        assert isinstance(search, str)
        self.search = search
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute(self, user: CMHTTPUser):
        """Search, and walk through the results."""
        for attempt in range(1, 100):
            book = self._find_book(user)
            if book is not None:
                return self._process_book(user, book)

        raise Exception("Unable to find a suitable book to bookmark.")

    def _process_book(self, user: CMHTTPUser, book: CMBook):
        self._process_book_create_loan(user, book)

        try:
            self._process_book_write_bookmarks(user, book)
        finally:
            self._process_book_revoke(user, book)

    def _process_book_revoke(self, user: CMHTTPUser, book: CMBook):
        if book.revoke_link is None:
            return

        self.logger.info(f"revoking loan {book.revoke_link}")
        response0 = user.client.get(
            book.revoke_link, headers=user.authentication.headers_required()
        )
        response0.raise_for_status()

    def _process_book_create_loan(self, user: CMHTTPUser, book: CMBook):
        self.logger.info(f"loan {book.borrow_link}")

        # Hit the borrow link. The server will return an OPDS feed entry containing that book.
        headers = user.authentication.headers_required()
        response0 = user.client.get(book.borrow_link, headers=headers)
        response0.raise_for_status()

        # Find the revocation link so that we can clean up the loan at the end of the test.
        book_entry = atoma.parse_atom_bytes(bytes(response0.text, "utf-8"))
        for link in book_entry.links:
            if link.rel == "http://librarysimplified.org/terms/rel/revoke":
                self.logger.info(f"found revocation link {link.href}")
                book.revoke_link = link.href

        if not book.revoke_link:
            self.logger.warn("could not find a revocation link for the loan")

        # Hit the loans feed so that we can find an annotations link.
        auth = user.auth_document
        assert auth
        shelf = auth.links.get(CMAuthenticationLinkType.SHELF)
        response1 = user.client.get(shelf, headers=headers)
        response1.raise_for_status()

        loans_feed = atoma.parse_atom_bytes(bytes(response1.text, "utf-8"))
        for link in loans_feed.links:
            if link.rel == "http://www.w3.org/ns/oa#annotationService":
                book.annotations_link = link.href

    def _process_book_write_bookmarks(self, user: CMHTTPUser, book: CMBook):
        bookmark_id = uuid.uuid4()
        source = uuid.uuid4()
        device = uuid.uuid4()

        post_headers = {}
        post_headers[
            "content-type"
        ] = 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"'
        for key, value in user.authentication.headers_required().items():
            post_headers[key] = value

        self.logger.info("writing lots of bookmarks")
        for write in range(1, 100):
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            bookmark = CMBookmark(
                id=str(bookmark_id),
                target=CMBookmarkTarget(
                    locator=CMLocatorPage(write), source=book.book_id
                ),
                motivation=CMMotivation.BOOKMARKING,
                body=CMBookmarkBody(device_id=str(device), time=timestamp, others={}),
            )

            response = user.client.post(
                book.annotations_link,
                data=json.dumps(bookmark.to_json_dict()),
                headers=post_headers,
            )

            if response.status_code >= 400:
                self.logger.error(f"{response.text}")
                response.raise_for_status()

    def _find_book(self, user: CMHTTPUser) -> Optional[CMBook]:
        term = Words.get()
        query = f"{self.search}&q={term}"
        self.logger.info(f"search {query}")

        response = user.client.get(query)
        response.raise_for_status()

        content_type = response.headers.get("content-type")
        self.logger.info(f"{content_type}")
        if content_type.startswith("application/atom+xml"):
            return self._handle_atom_feed(user, response)

        return None

    def _handle_atom_feed(self, user: CMHTTPUser, response) -> Optional[CMBook]:
        feed = atoma.parse_atom_bytes(response.text.encode("utf-8"))
        current = feed
        while True:
            self.logger.info(f"current {feed.id_}")
            search_results = self._process_atom_feed(user, current)
            if search_results.book is not None:
                self.logger.info(f"found a book: {search_results.book.borrow_link}")
                return search_results.book
            if search_results.next_feed is None:
                self.logger.info("ran out of search feed entries")
                break
            current = search_results.next_feed
        return None

    def _process_atom_feed(
        self, user: CMHTTPUser, feed: AtomFeed
    ) -> CMSearchAndBookmarkResults:
        for entry in feed.entries:
            for link in entry.links:
                if link.rel == "http://opds-spec.org/acquisition/borrow":
                    self.logger.info(f"found borrowable book {entry.id_}")
                    return CMSearchAndBookmarkResults(
                        book=CMBook(
                            borrow_link=link.href,
                            book_id=entry.id_,
                            revoke_link=None,
                            annotations_link=None,
                        ),
                        next_feed=None,
                    )

        for link in feed.links:
            if link.rel == "next":
                self.logger.info(f"next {link.href}")
                response_next = user.client.get(link.href)
                response_next.raise_for_status()
                return CMSearchAndBookmarkResults(
                    book=None,
                    next_feed=atoma.parse_atom_bytes(
                        response_next.text.encode("utf-8")
                    ),
                )

        return CMSearchAndBookmarkResults(book=None, next_feed=None)

    @classmethod
    def find_search_link(cls, user: CMHTTPUser, url: str) -> Optional[str]:
        response = user.client.get(url)
        response.raise_for_status()

        content_type = response.headers.get("content-type")
        if content_type.startswith("application/atom+xml"):
            feed = atoma.parse_atom_bytes(response.text.encode("utf-8"))
            for link in feed.links:
                if link.rel == "search":
                    return link.href

        return None
