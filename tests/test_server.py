import os
from dizzy.daemon import Server
from dizzy.daemon.client.basic import DizzyClient
import logging
import pytest
import threading

logging.basicConfig(level=logging.DEBUG)


def busy_client():
    client = DizzyClient(port=7777)
    while True:
        try:
            response = client.request_task("uno", "A")
        except Exception:
            break


def start_server():
    from dizzy.daemon import Server

    server = Server(port=7777)
    server.run()


class TestServer:
    def setup_method(self):
        self.server = Server(port=7777)

        # start the async server in a separate thread
        def async_server():
            import asyncio

            asyncio.run(self.server.run())

        self.server_thread = threading.Thread(target=async_server)
        self.server_thread.start()

        self.client = DizzyClient(port=7777)

    def teardown_method(self):
        self.client.stop()
        self.server.stop()
        try:
            self.server_thread.join()
        except KeyboardInterrupt:
            pass

    def test_server(self):
        response = self.client.request_task("uno", "A")
        assert response["status"] == "completed"

    # def test_not_blocking(self):
    #     # start 10 busy client threads
    #     threads = []
    #     for i in range(10):
    #         t = threading.Thread(target=busy_client)
    #         t.start()
    #         threads.append(t)

    #     for t in threads:
    #         t.cancel()
    #         t.join()


if __name__ == "__main__":
    pytest.main()
