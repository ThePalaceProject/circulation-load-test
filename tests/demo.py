from circulation_load_test.cm.basic import CMTests
from circulation_load_test.common.cmauthdocument import CMAuthenticationLinkType
from circulation_load_test.common.cmfeedwalk import CMFeedWalk
from circulation_load_test.common.cmlogin import CMLogin
from circulation_load_test.common.cmsearch import CMSearch
from locust.env import Environment

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    env = Environment()
    user = CMTests(env)
    document = CMLogin.login(user)
    root = document.links[CMAuthenticationLinkType.CATALOG]
    search_link = CMSearch.find_search_link(user, root)
    search = CMSearch(search_link)
    search.execute(user)


if __name__ == "__main__":
    main()
