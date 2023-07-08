import asyncio
import os
import time
from dizzy.daemon import Server
from dizzy.daemon.client.asy import SimpleAsyncClient
import logging
import pytest
import threading

logging.basicConfig(level=logging.DEBUG)


def busy_client():
    client = SimpleAsyncClient(port=7777)
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
        self.client = SimpleAsyncClient(port=7777)

        # start the async server in a separate thread
        def async_server():
            import asyncio

            asyncio.run(self.server.run())

        def async_client():
            import asyncio

            asyncio.run(self.client.run())

        self.server_thread = threading.Thread(target=async_server)
        self.client_thread = threading.Thread(target=async_client)

        self.server_thread.start()
        self.client_thread.start()

    def teardown_method(self):
        self.client.stop()
        self.server.stop()
        try:
            self.client_thread.join()
            self.server_thread.join()
        except KeyboardInterrupt:
            pass

    # @pytest.mark.skip(reason="Broken, works but won't always shut down. If you enable, you might need to Ctrl+C")
    def test_server(self):
        # response = await self.client.request_task("uno", "A")
        # run the coroutine in the event loop
        asyncio.run(self.client.request_task("uno", "A"))
        while len(self.client.history) == 0:
            time.sleep(0.1)

        _, response = self.client.history[0]
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
