import asyncio
import os
import time
from dizzy.daemon import SimpleRequestServer
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
            time.sleep(5)
        except Exception:
            break


def start_server():
    from dizzy.daemon import SimpleRequestServer

    server = SimpleRequestServer(port=7777)
    server.run()


class TestServer:
    def setup_method(self):
        self.server = SimpleRequestServer(port=7777)
        self.client = SimpleAsyncClient(port=7777)

        # start the async server in a separate thread
        def async_server():
            asyncio.run(self.server.run())

        def async_client():
            asyncio.run(self.client.run())

        # self.server_thread = threading.Thread(target=async_server)
        # self.client_thread = threading.Thread(target=async_client)
        #
        # self.server_thread.start()
        # self.client_thread.start()
        #
        # Executors instead of threads:
        self.loop = asyncio.new_event_loop()
        self.loop.run_in_executor(None, self.server.run)
        self.loop.run_in_executor(None, self.client.run)

    def teardown_method(self):
        self.client.stop()
        self.server.stop()

        self.loop.stop()

        # try:
        #     self.client_thread.join()
        #     self.server_thread.join()
        # except KeyboardInterrupt:
        #     pass

    @pytest.mark.skip(
        reason="Broken, works but won't always shut down. If you enable, you might need to Ctrl+C"
    )
    def test_server(self):
        # response = await self.client.request_task("uno", "A")
        # run the coroutine in the event loop
        self.loop.run_in_executor(None, self.client.request_task, "uno", "A")
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
