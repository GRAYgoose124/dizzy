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
        while self.running:
            if self.socket.closed:
                break

            try:
                request = self.request_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0)
                continue

            response = await self.send_request(request)
            self.process_response(request, response)
            self.request_queue.task_done()
            await asyncio.sleep(0)

    async def send_request(self, request):
        self.socket.send_json(request)
        response = await self.socket.recv()
        return json.loads(response.decode())

    def process_response(self, request, response):
        self.history.append((request, response))
        logger.info(f"Received response for request: {request}")
        logger.info(f"Response: {response}")

    async def request_workflow(self, entity: str = "einz", workflow: str = "einzy"):
        request = {"entity": entity, "workflow": workflow}
        await self.request_queue.put(request)

    async def request_task(self, service: str = "common", task: str = "echo"):
        request = {"service": service, "task": task}
        await self.request_queue.put(request)
