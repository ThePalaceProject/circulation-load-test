import logging

from locust import FastHttpUser
from typing import Set
from typing import List

import random
import atoma

from atoma.atom import AtomLink

class CMFeedWalk:
    """A class to walk randomly through an OPDS feed."""

    def __init__(self, link_start: str, allowed_link_relations: Set[str], maximum_visits: int):
        assert isinstance(link_start, str)
        assert isinstance(allowed_link_relations, Set)
        assert isinstance(maximum_visits, int)
        self.maximum_visits = maximum_visits
        self.link_start = link_start
        self.allowed_link_relations = allowed_link_relations
        self.visited: Set[str] = set()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _execute(self, link: str, user: FastHttpUser):
        if link in self.visited:
            return

        self.visited.add(link)
        if len(self.visited) >= self.maximum_visits:
            return

        self.logger.info(f"get {link}")
        response = user.client.get(link)
        response.raise_for_status()

        content_type = response.headers.get('content-type')
        self.logger.debug(f'content type {content_type}')
        if content_type.startswith('application/atom+xml'):
            feed = atoma.parse_atom_bytes(response.text.encode('utf-8'))

            raw_links: List[AtomLink] = []
            for link in feed.links:
                raw_links.append(link)
            for entry in feed.entries:
                for link in entry.links:
                    raw_links.append(link)

            candidates: List[AtomLink] = list(filter(lambda link: self._is_candidate_link(link), raw_links))
            self.logger.debug(f'found {str(len(candidates))} candidate links')
            random.shuffle(candidates)
            for candidate in candidates:
                assert isinstance(candidate, AtomLink)
                self._execute(candidate.href, user)


    def _is_candidate_link(self, link: AtomLink) -> bool:
        return link.rel in self.allowed_link_relations

    def execute(self, user: FastHttpUser):
        """Start walking."""
        self.visited.clear()
        self._execute(self.link_start, user)