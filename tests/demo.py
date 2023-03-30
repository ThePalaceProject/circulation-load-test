import logging

from locust.env import Environment

from circulation_load_test.cm.basic import CMTests
from circulation_load_test.common.cmlogin import CMLogin
from circulation_load_test.common.cmsearchbookmark import CMSearchAndBookmark
from circulation_load_test.common.cmuser import CMAuthenticationLinkType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#
# This is a small demo file that shows how the various bits of "common" library
# code can be called without having to go through the Locust frontend. This is
# just for convenience during development.
#


def main():
    env = Environment()
    user = CMTests(env)
    document = CMLogin.login(user)
    root = document.links[CMAuthenticationLinkType.CATALOG]
    search_link = CMSearchAndBookmark.find_search_link(user, root)
    search = CMSearchAndBookmark(search_link)
    search.execute(user)


if __name__ == "__main__":
    main()
