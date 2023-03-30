import atoma
from atoma.atom import AtomLink

from circulation_load_test.common.cmuser import (
    CMAuthDocument,
    CMAuthenticationLinkType,
    CMAuthenticationType,
    CMHTTPUser,
)
from circulation_load_test.common.config import CMConfiguration, Configurations


class CMLogin:
    @staticmethod
    def login(user: CMHTTPUser) -> CMAuthDocument:
        config = Configurations.get()
        cm: CMConfiguration = config.circulation_manager

        # Fetch the root feed. This will typically contain a link to an authentication document.
        response = user.client.get(cm.address)
        response.raise_for_status()

        text = response.text
        feed = atoma.parse_atom_bytes(bytes(text, "utf-8"))
        for link in feed.links:
            if link.rel == "http://opds-spec.org/auth/document":
                return CMLogin._handle_auth_document(user, link)

        # Synthesize a fake authentication document that supplies a starting link
        links = {}
        links[CMAuthenticationLinkType.CATALOG] = cm.address
        document = CMAuthDocument(auth_types={}, links=links)
        user.auth_document = document
        return document

    @staticmethod
    def _handle_auth_document(user: CMHTTPUser, link: AtomLink) -> CMAuthDocument:
        response = user.client.get(link.href)
        text = response.text
        document = CMAuthDocument.parse(text)

        # There may not be any required authentication.
        if len(document.auth_types) == 0:
            user.auth_document = document
            return document

        # We know how to handle basic authentication, so use it.
        basic = document.auth_types.get(CMAuthenticationType.BASIC)
        if basic:
            basic.authenticate(user)
            user.auth_document = document
            return document

        raise ValueError("No supported authentication mechanisms.")
