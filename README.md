# Palace Backend Load Testing

This repo contains a set of load tests that can be run against the Palace backend
to simulate user load on the servers.

## Locust

These tests are built in Python using [Locust](https://locust.io/). The Locust page
contains good [documentation](https://docs.locust.io/en/stable/writing-a-locustfile.html)
about writing tests.

## Running tests

Install dependencies and run Locust:

```shell
poetry install
poetry run locust
```

The locust dashboard will then be available at: `http://localhost:8089`.

## Test details

The currently available load tests are documented inline in the
[locustfile](locustfile.py).
