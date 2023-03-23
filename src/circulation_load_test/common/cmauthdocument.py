import json
from enum import Enum
from abc import ABC
from abc import abstractmethod
from base64 import b64encode
from locust import FastHttpUser

from circulation_load_test.common.config import Configurations

from typing import Dict
from typing import Mapping

REL_USER_PROFILE = 'http://librarysimplified.org/terms/rel/user-profile'

class CMAuthenticationType(Enum):
    BASIC = 1


class CMAuthenticationLinkType(Enum):
    CATALOG = 1
    USER_PROFILE = 2
    SHELF = 3


class CMAuthentication(ABC):
    @abstractmethod
    def authenticate(self, user: FastHttpUser):
        pass

    @abstractmethod
    def type(self) -> CMAuthenticationType:
        pass


class CMAuthenticationBasic(CMAuthentication):

    def __init__(self, user_profile_link: str):
        self._user_profile_link = user_profile_link

    @staticmethod
    def _basic_auth(username, password):
        token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
        return f'Basic {token}'

    def authenticate(self, user: FastHttpUser):
        cm_config = Configurations.get().circulation_manager
        cm_user = cm_config.user_primary()

        headers = {}
        headers['Authorization'] = self._basic_auth(cm_user.name, cm_user.password)
        response = user.client.get(self._user_profile_link, headers=headers)
        if response.status_code >= 400:
            response.raise_for_status()

    def type(self) -> CMAuthenticationType:
        return CMAuthenticationType.BASIC

    @staticmethod
    def parse(auth: dict, links: Mapping[CMAuthenticationLinkType, str]) -> "CMAuthenticationBasic":
        user_profile = links[CMAuthenticationLinkType.USER_PROFILE]
        if user_profile:
            return CMAuthenticationBasic(user_profile)
        else:
            raise ValueError("Missing a required link with rel " + REL_USER_PROFILE)


class CMAuthDocument:

    def __init__(self, auth_types: Mapping[CMAuthenticationType, CMAuthentication], links: Mapping[CMAuthenticationLinkType, str]):
        self.auth_types = auth_types
        self.links = links

    @staticmethod
    def parse(text: str) -> "CMAuthDocument":
        doc = json.loads(text)

        links = {}
        for link in doc['links']:
            if link['rel'] == 'start':
                links[CMAuthenticationLinkType.CATALOG] = link['href']
            if link['rel'] == 'http://opds-spec.org/shelf':
                links[CMAuthenticationLinkType.SHELF] = link['href']
            if link['rel'] == REL_USER_PROFILE:
                links[CMAuthenticationLinkType.USER_PROFILE] = link['href']

        authentications = {}
        for auth in doc['authentication']:
            if auth['type'] == 'http://opds-spec.org/auth/basic':
                authentications[CMAuthenticationType.BASIC] = CMAuthenticationBasic.parse(auth, links)

        return CMAuthDocument(authentications, links)
