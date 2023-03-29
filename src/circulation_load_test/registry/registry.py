from urllib.parse import urlparse

from gevent.pool import Pool
from locust import task

from circulation_load_test.common.cmuser import CMHTTPUser


class RegistryTests(CMHTTPUser):

    host = "https://registry.palaceproject.io/"

    def fetch(self, url):
        parsed = urlparse(url)
        name = f"{parsed.hostname}/[library]/authentication_document"
        self.client.get(url, name=name)

    @task
    def first_open_app(self):
        """
        Simulates a user opening the app for the first time, or reopening the app
        after the cache has expired. Based on testing with iOS app version 1.0.25
        using MITMProxy to see what requests are made.
        """
        response = self.client.get("/libraries")
        json = response.json()
        if "catalogs" not in json:
            response.failure("No catalogs key")

        authentication_documents = []
        for catalog in json["catalogs"]:
            for link in catalog["links"]:
                if (
                    "type" in link
                    and link["type"] == "application/vnd.opds.authentication.v1.0+json"
                ):
                    authentication_documents.append(link["href"])

        # Concurrently fetch 10 documents at once
        pool = Pool(size=10)
        for href in authentication_documents:
            pool.spawn(self.fetch, href)
        pool.join()
