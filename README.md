# Palace Backend Load Testing

This repo contains a set of load tests that can be run against the Palace backend
to simulate user load on the servers.

Please read the [fair warning](#fair-warning)!

## Locust

These tests are built in Python using [Locust](https://locust.io/). The Locust page
contains good [documentation](https://docs.locust.io/en/stable/writing-a-locustfile.html)
about writing tests.

## Running Load Tests

Install dependencies:

```shell
poetry install
```

Write a [configuration file](#configuration-file), place its fully-qualified path in
the `CIRCULATION_LOAD_CONFIGURATION_FILE` environment variable, and run Locust:

```shell
poetry run \
  env CIRCULATION_LOAD_CONFIGURATION_FILE=$(realpath hosts.json) \
  locust
```

The locust dashboard will then be available at: `http://localhost:8089`.

## Fair Warning

*Do not run this code against production servers!*

*Some tests involve borrowing books. Borrowing a book, on many CMs, will consume a license. This may cost money!*

A good example is the [bookmark tests](src/circulation_load_test/common/cmsearchbookmark.py); in order to create
bookmarks, the bookmarks must be associated with a loan. The bookmark test loans a random book, adds a lot of
bookmarks, and then returns the book.

## Configuration File

The configuration file specifies the [Library Registry](https://github.com/ThePalaceProject/library-registry)
and [Circulation Manager](https://github.com/ThePalaceProject/circulation) instances against which tests will
run. For the CM, a list of users (along with their passwords) must also be specified. One user must be declared
as _primary_, as some tests will use this user as the default user for various reasons.

The configuration file also contains a list of library identifiers that must exist on the target CM. These
are used by tests that want to try making requests to random libraries.

```json
{
  "registry": {
    "host": "http://registry.example.com/"
  },
  "circulation_manager": {
    "host": "http://cm.example.com/",
    "users": {
      "user0": {
        "primary": "true",
        "password": "abcd1234"
      },
      "user1": {
        "password": "abcd1234"
      },
      "user2": {
        "password": "abcd1234"
      }
    },
    "library_identifiers": [
      "Library1",
      "Library2",
      "Library3"
    ]
  }
}
```

## Running Unit Tests

Unit tests can be executed using [tox](https://pypi.org/project/tox/). At the time of writing, the only
available environment is `py310` (which tests against Python 3.10.*):

```sh
tox -e py310
```
