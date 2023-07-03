import os
from dizzy.daemon import Server
from dizzy.daemon.client.basic import DizzyClient
import logging
import threading

logging.basicConfig(level=logging.DEBUG)


class TestServer:
    def setup_method(self):
        self.server = Server(port=7777)
        # start a server in a separate thread
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.start()

        self.client = DizzyClient(port=7777)

    def teardown_method(self):
        self.server.stop()
        self.server_thread.join()

    def test_server(self):
        response = self.client.request_task("uno", "A")
        assert response["status"] == "completed"
