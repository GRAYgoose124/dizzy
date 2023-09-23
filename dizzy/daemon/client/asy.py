import json
import zmq
import zmq.asyncio
import asyncio
import logging

logger = logging.getLogger(__name__)

from ..protocol import Request, Response


class SimpleAsyncClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton"""
        if cls._instance is None:
            cls._instance = super(SimpleAsyncClient, cls).__new__(cls)

        return cls._instance

    def __init__(self, address="localhost", port=5555):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{address}:{port}")

        self.request_queue = asyncio.Queue()
        self.history = []

        self.running = False
        self.loop_task = None

    def stop(self):
        self.running = False
        self.socket.close()
        self.context.term()

    async def run(self):
        self.running = True
        while self.running and not self.socket.closed:
            try:
                request = self.request_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue

            response = await self.send_request(request)
            self._process_response(request, response)
            await asyncio.sleep(0)

    async def send_request(self, request):
        self.socket.send_json(request)
        response = await self.socket.recv()
        return json.loads(response.decode())

    def _process_response(self, request, response):
        self.history.append((request, response))
        logger.info(f"Received response for request: {request}")
        logger.info(f"Response: {response}")
        self.request_queue.task_done()

    def _build_workflow_request(self, entity: str, workflow: str):
        return {"entity": entity, "workflow": workflow}

    def _build_task_request(self, service: str, task: str):
        return {"service": service, "task": task}

    async def request_workflow(self, entity: str = "einz", workflow: str = "einzy"):
        request = self._build_workflow_request(entity, workflow)
        await self.request_queue.put(request)

    async def request_task(self, service: str = "common", task: str = "echo"):
        request = self._build_task_request(service, task)
        await self.request_queue.put(request)

    def sync_request_workflow(self, entity: str = "einz", workflow: str = "einzy"):
        request = self._build_workflow_request(entity, workflow)
        return asyncio.run(self.send_request(request))

    def sync_request_task(self, service: str = "common", task: str = "echo"):
        request = self._build_task_request(service, task)
        return asyncio.run(self.send_request(request))
