from locust import tag, task

from circulation_load_test.common.cmfeedwalk import CMFeedWalk
from circulation_load_test.common.cmlogin import CMLogin
from circulation_load_test.common.cmsearch import CMSearch
from circulation_load_test.common.cmsearchbookmark import CMSearchAndBookmark
from circulation_load_test.common.cmuser import CMAuthenticationLinkType, CMHTTPUser
from circulation_load_test.common.config import Configurations


class CMTests(CMHTTPUser):

    host = Configurations.get().circulation_manager.address

    @task
    @tag("login")
    def login(self):
        """Check how long it takes to log in to the target CM."""
        CMLogin.login(self)

    @task
    @tag("feeds")
    def random_feed_walk(self):
        """Walk through feeds at random until reaching a maximum depth."""
        document = CMLogin.login(self)
        root = document.links[CMAuthenticationLinkType.CATALOG]
        walk = CMFeedWalk(
            root,
            allowed_link_relations={"collection", "related", "alternate"},
            maximum_visits=10,
        )
        walk.execute(self)

    @task
    @tag("search")
    def random_search(self):
        """Perform a random search and walk through all the results."""
        document = CMLogin.login(self)
        root = document.links[CMAuthenticationLinkType.CATALOG]
        search_link = CMSearch.find_search_link(self, root)
        search = CMSearch(search_link)
        search.execute(self)

    @task
    @tag("bookmarks")
    def bookmarks(self):
        """Borrow an open access book, and start producing a lot of bookmarks."""
        document = CMLogin.login(self)
        root = document.links[CMAuthenticationLinkType.CATALOG]
        search_link = CMSearchAndBookmark.find_search_link(self, root)
        search = CMSearchAndBookmark(search_link)
        search.execute(self)
