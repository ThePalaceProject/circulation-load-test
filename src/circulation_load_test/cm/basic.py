from locust import FastHttpUser, task, tag

from circulation_load_test.common.cmauthdocument import CMAuthenticationLinkType
from circulation_load_test.common.config import Configurations
from circulation_load_test.common.cmlogin import CMLogin
from circulation_load_test.common.cmsearch import CMSearch

class CMTests(FastHttpUser):

    host = Configurations.get().circulation_manager.address

    @task
    @tag('login')
    def login(self):
        """Check how long it takes to log in to the target CM."""
        CMLogin.login(self)

    @task
    @tag('feeds')
    def random_feed_walk(self):
        """Walk through feeds at random until reaching a maximum depth."""
        document = CMLogin.login(self)
        root = document.links[CMAuthenticationLinkType.CATALOG]
        walk = CMFeedWalk(root, allowed_link_relations={'collection', 'related', 'alternate'}, maximum_visits=10)
        walk.execute(user)

    @task
    @tag('search')
    def random_search(self):
        """Perform a random search and walk through all the results."""
        document = CMLogin.login(self)
        root = document.links[CMAuthenticationLinkType.CATALOG]
        search_link = CMSearch.find_search_link(self, root)
        search = CMSearch(search_link)
        search.execute(self)
