import logging
from typing import Optional

import atoma
from atoma.atom import AtomFeed

from circulation_load_test.common.cmuser import CMHTTPUser
from circulation_load_test.common.words import Words


class CMSearch:
    """A class to walk through search results."""

    def __init__(self, search: str):
        assert isinstance(search, str)
        self.search = search
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute(self, user: CMHTTPUser):
        """Search, and walk through the results."""
        term = Words.get()
        query = f"{self.search}&q={term}"
        self.logger.info(f"search {query}")

        response = user.client.get(query)
        response.raise_for_status()

        content_type = response.headers.get("content-type")
        self.logger.info(f"{content_type}")
        if content_type.startswith("application/atom+xml"):
            return self._handle_atom_feed(user, response)

    def _handle_atom_feed(self, user: CMHTTPUser, response):
        feed = atoma.parse_atom_bytes(response.text.encode("utf-8"))
        current = feed
        while True:
            self.logger.info(f"current {feed.id_}")
            current = self._process_atom_feed(user, current)
            if not current:
                break

        self.logger.info(f"finished")

    def _process_atom_feed(
        self, user: CMHTTPUser, feed: AtomFeed
    ) -> Optional[AtomFeed]:
        for link in feed.links:
            if link.rel == "next":
                self.logger.info(f"next {link.href}")
                response_next = user.client.get(link.href)
                response_next.raise_for_status()
                return atoma.parse_atom_bytes(response_next.text.encode("utf-8"))
        return None

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
