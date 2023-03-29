import logging
from dataclasses import dataclass
from typing import Optional

import atoma
from atoma.atom import AtomFeed

from circulation_load_test.common.cmuser import CMHTTPUser
from circulation_load_test.common.words import Words


@dataclass
class CMSearchAndBorrowResults:
    book_link: Optional[str]
    next_feed: Optional[AtomFeed]


class CMSearchAndBorrow:
    """Search for a book that we can borrow, and borrow it."""

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

        raise Exception("Unable to find a suitable book to borrow.")

    def _process_book(self, user: CMHTTPUser, book: str):
        return

    def _find_book(self, user: CMHTTPUser) -> Optional[str]:
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

    def _handle_atom_feed(self, user: CMHTTPUser, response) -> Optional[str]:
        feed = atoma.parse_atom_bytes(response.text.encode("utf-8"))
        current = feed
        while True:
            self.logger.info(f"current {feed.id_}")
            search_results = self._process_atom_feed(user, current)
            if search_results.book_link is not None:
                self.logger.info(f"found a book link: {search_results.book_link}")
                return search_results.book_link
            if search_results.next_feed is None:
                self.logger.info("ran out of search feed entries")
                break
            current = search_results.next_feed
        return None

    def _process_atom_feed(
        self, user: CMHTTPUser, feed: AtomFeed
    ) -> CMSearchAndBorrowResults:
        for entry in feed.entries:
            for link in entry.links:
                if link.rel == "http://opds-spec.org/acquisition/borrow":
                    return CMSearchAndBorrowResults(book_link=link.href, next_feed=None)

        for link in feed.links:
            if link.rel == "next":
                self.logger.info(f"next {link.href}")
                response_next = user.client.get(link.href)
                response_next.raise_for_status()
                return CMSearchAndBorrowResults(
                    book_link=None,
                    next_feed=atoma.parse_atom_bytes(
                        response_next.text.encode("utf-8")
                    ),
                )

        return CMSearchAndBorrowResults(book_link=None, next_feed=None)

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
