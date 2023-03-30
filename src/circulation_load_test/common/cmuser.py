import json
from abc import ABC, abstractmethod
from base64 import b64encode
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

from locust import FastHttpUser
from locust.env import Environment

from circulation_load_test.common.config import Configurations

REL_USER_PROFILE = "http://librarysimplified.org/terms/rel/user-profile"


class CMAuthenticationType(Enum):
    BASIC = 1


class CMAuthenticationLinkType(Enum):
    CATALOG = 1
    USER_PROFILE = 2
    SHELF = 3


class CMAuthentication(ABC):
    @abstractmethod
    def authenticate(self, user: "CMHTTPUser"):
        pass

    @abstractmethod
    def headers_required(self) -> Mapping[str, str]:
        pass

    @abstractmethod
    def type(self) -> CMAuthenticationType:
        pass


class CMAuthenticationBasic(CMAuthentication):
    def __init__(self, user_profile_link: str):
        self._user_profile_link = user_profile_link

    @staticmethod
    def _basic_auth(username, password):
        token = b64encode(f"{username}:{password}".encode()).decode("ascii")
        return f"Basic {token}"

    def authenticate(self, user: "CMHTTPUser"):
        cm_config = Configurations.get().circulation_manager
        cm_user = cm_config.user_primary()

        #
        # Fetch the user profile. This "logs in" by checking the credentials.
        #
        self.auth_header = self._basic_auth(cm_user.name, cm_user.password)
        headers0 = {"Authorization": self.auth_header}
        response0 = user.client.get(self._user_profile_link, headers=headers0)
        if response0.status_code >= 400:
            response0.raise_for_status()

        #
        # Save the authentication scheme
        #
        user.authentication = self

        #
        # Update the patron settings to enable annotations.
        #
        post_settings = {"settings": {"simplified:synchronize_annotations": True}}
        post_data = json.dumps(post_settings)
        headers1 = {
            "Authorization": self.auth_header,
            "Content-Type": "vnd.librarysimplified/user-profile+json",
        }
        response1 = user.client.put(
            self._user_profile_link, data=post_data, headers=headers1
        )
        if response1.status_code >= 400:
            response1.raise_for_status()

        #
        # Fetch the user profile again.
        #
        headers2 = {"Authorization": self.auth_header}
        response2 = user.client.get(self._user_profile_link, headers=headers2)
        if response2.status_code >= 400:
            response2.raise_for_status()

        data = json.loads(response2.text)
        user.user_profile = CMPatronUserProfile(data)

    def headers_required(self) -> Mapping[str, str]:
        return {"Authorization": self.auth_header}

    def type(self) -> CMAuthenticationType:
        return CMAuthenticationType.BASIC

    @staticmethod
    def parse(
        auth: dict, links: Mapping[CMAuthenticationLinkType, str]
    ) -> "CMAuthenticationBasic":
        user_profile = links[CMAuthenticationLinkType.USER_PROFILE]
        if user_profile:
            return CMAuthenticationBasic(user_profile)
        else:
            raise ValueError("Missing a required link with rel " + REL_USER_PROFILE)


class CMAuthDocument:
    def __init__(
        self,
        auth_types: Mapping[CMAuthenticationType, CMAuthentication],
        links: Mapping[CMAuthenticationLinkType, str],
    ):
        self.auth_types = auth_types
        self.links = links

    @staticmethod
    def parse(text: str) -> "CMAuthDocument":
        doc = json.loads(text)

        links = {}
        for link in doc["links"]:
            if link["rel"] == "start":
                links[CMAuthenticationLinkType.CATALOG] = link["href"]
            if link["rel"] == "http://opds-spec.org/shelf":
                links[CMAuthenticationLinkType.SHELF] = link["href"]
            if link["rel"] == REL_USER_PROFILE:
                links[CMAuthenticationLinkType.USER_PROFILE] = link["href"]

        authentications = {}
        for auth in doc["authentication"]:
            if auth["type"] == "http://opds-spec.org/auth/basic":
                authentications[
                    CMAuthenticationType.BASIC
                ] = CMAuthenticationBasic.parse(auth, links)

        return CMAuthDocument(authentications, links)


@dataclass
class CMPatronUserProfile:
    settings: Mapping[str, Any]


class CMHTTPUser(FastHttpUser):
    """A CM user."""

    auth_document: Optional[CMAuthDocument]
    user_profile: Optional[CMPatronUserProfile]
    _authentication: Optional[CMAuthentication]

    def __init__(self, environment: Environment):
        super().__init__(environment=environment)
        self.auth_document = None
        self.user_profile = None
        self._authentication = None

    @property
    def authentication(self) -> CMAuthentication:
        if self._authentication is None:
            raise ValueError("User has not yet logged in!")
        return self._authentication

    @authentication.setter
    def authentication(self, value: CMAuthentication):
        assert value is not None
        self._authentication = value
