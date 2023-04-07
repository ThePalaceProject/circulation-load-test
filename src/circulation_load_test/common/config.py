import json
import os
from typing import Any, Dict, Optional, Set


class CMUser:
    name: str
    password: str

    def __init__(self, name: str, password: str, primary: bool):
        super().__init__()
        assert isinstance(name, str)
        assert isinstance(password, str)
        assert isinstance(primary, bool)
        self.name = name
        self.password = password
        self.primary = primary

    @staticmethod
    def parse(name: str, data: Any) -> "CMUser":
        primary = data.get("primary")
        primary_b = False
        if primary is not None:
            if primary.upper() == "TRUE":
                primary_b = True
            elif primary.upper() == "FALSE":
                primary_b = False
            else:
                raise ValueError(
                    "'primary' must be 'true' or 'false' (got " + primary + ")"
                )

        return CMUser(name, data["password"], primary_b)


class RConfiguration:
    address: str

    def __init__(self, address: str):
        super().__init__()
        assert isinstance(address, str)
        self.address = address

    @staticmethod
    def parse(data: Any) -> "RConfiguration":
        address = data["host"]
        return RConfiguration(address)


class CMConfiguration:
    address: str
    users: Dict[str, CMUser]
    library_identifiers: Set[str]

    def __init__(
        self, address: str, users: Dict[str, CMUser], library_identifiers: Set[str]
    ):
        super().__init__()
        assert isinstance(address, str)
        assert isinstance(users, dict)
        self.address = address
        self.users = users
        self.library_identifiers = library_identifiers

    def user_primary(self) -> CMUser:
        for name in self.users.keys():
            if self.users[name].primary:
                return self.users[name]

        raise ValueError("No users defined!")

    @staticmethod
    def parse(data: Any) -> "CMConfiguration":
        address = data["host"]

        library_ids_in = data["library_identifiers"]
        library_ids = set(library_ids_in)

        users_primary = False
        users_in = data["users"]
        users = {}
        for name, value in users_in.items():
            user = CMUser.parse(name, value)
            if users_primary:
                if user.primary:
                    raise ValueError("Multiple primary users defined!")

            users_primary = users_primary or user.primary
            users[name] = user

        if not users_primary:
            raise ValueError("Exactly one primary user must be defined!")

        return CMConfiguration(address, users, library_ids)


class Configuration:
    circulation_manager: CMConfiguration
    registry: RConfiguration

    def __init__(self, circulation_manager: CMConfiguration, registry: RConfiguration):
        super().__init__()
        assert isinstance(circulation_manager, CMConfiguration)
        assert isinstance(registry, RConfiguration)
        self.circulation_manager = circulation_manager
        self.registry = registry

    @staticmethod
    def load(path: str) -> "Configuration":
        with open(path) as f:
            return Configuration._parse(json.load(f))

    @staticmethod
    def _parse(data: Any) -> "Configuration":
        cm = CMConfiguration.parse(data["circulation_manager"])
        r = RConfiguration.parse(data["registry"])
        return Configuration(cm, r)


class Configurations:
    _configuration: Optional[Configuration] = None

    @classmethod
    def get(cls) -> Configuration:
        if cls._configuration:
            return cls._configuration

        location = os.getenv("CIRCULATION_LOAD_CONFIGURATION_FILE")
        if not location:
            raise ValueError(
                "CIRCULATION_LOAD_CONFIGURATION_FILE environment variable is undefined"
            )

        cls._configuration = Configuration.load(location)
        return cls._configuration

    @classmethod
    def clear(cls):
        cls._configuration = None
