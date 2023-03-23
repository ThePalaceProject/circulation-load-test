import os
from pathlib import Path

import pytest
from circulation_load_test.common.config import Configurations
from circulation_load_test.common.config import Configuration


class ConfigurationsFixture:

    def __init__(self, monkeypatch):
        self.monkeypatch = monkeypatch

    def load(self, name: str) -> Configuration:
        self.monkeypatch.setenv('CIRCULATION_LOAD_CONFIGURATION_FILE', name)
        return Configurations.get()

    def close(self):
        Configurations.clear()
        pass


@pytest.fixture(scope="function")
def configurations_fixture(monkeypatch):
    fixture = ConfigurationsFixture(monkeypatch)
    yield fixture
    fixture.close()


class TestConfigurations:
    def test_load_missing_environment(self, monkeypatch):
        monkeypatch.delenv('CIRCULATION_LOAD_CONFIGURATION_FILE', raising=False)
        with pytest.raises(ValueError):
            Configurations.get()

    def test_load_ok(self, configurations_fixture: ConfigurationsFixture):
        file = os.path.join(Path(__file__).parent, "hosts.json")
        config = configurations_fixture.load(file)
        assert "http://example1.example.com/" == config.circulation_manager.address
        assert 3 == len(config.circulation_manager.users)

    def test_load_bad_user_0(self, configurations_fixture: ConfigurationsFixture):
        file = os.path.join(Path(__file__).parent, "hosts_user_bad_0.json")
        with pytest.raises(ValueError):
            configurations_fixture.load(file)

    def test_load_bad_user_1(self, configurations_fixture: ConfigurationsFixture):
        file = os.path.join(Path(__file__).parent, "hosts_user_bad_1.json")
        with pytest.raises(ValueError):
            configurations_fixture.load(file)
