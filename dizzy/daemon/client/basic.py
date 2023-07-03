import json
import zmq


class DizzyClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton"""
        # if cls._instance is None:
        #     cls._instance = super(DizzyClient, cls).__new__(cls)

        # return cls._instance
        return super(DizzyClient, cls).__new__(cls)

    def __init__(self, address="localhost", port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

        self.socket.connect(f"tcp://{address}:{port}")

    def stop(self):
        self.socket.close()
        self.context.term()

    def request_workflow(self, entity: str = "einz", workflow: str = "einzy"):
        self.socket.send_json({"entity": entity, "workflow": workflow})
        return json.loads(self.socket.recv().decode())

    def request_task(self, service: str = "common", task: str = "echo"):
        self.socket.send_json({"service": service, "task": task})
        return json.loads(self.socket.recv().decode())
