import json
import zmq
import zmq.asyncio
import asyncio
import logging

logger = logging.getLogger(__name__)

from ..abstract_protocol import BaseProtocol, DefaultProtocol

class SimpleAsyncClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton"""
        if cls._instance is None:
            cls._instance = super(SimpleAsyncClient, cls).__new__(cls)

        return cls._instance

    def __init__(self, protocol: BaseProtocol = DefaultProtocol, address="localhost", port=5555):
        # If protocol is a class, instantiate it
        if isinstance(protocol, type):
            protocol = protocol()
        self.protocol = protocol
        assert isinstance(self.protocol, BaseProtocol), f"Protocol must be a subclass of BaseProtocol, got {type(self.protocol)}"

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
            request = await self.request_queue.get()

            response = await self.send_request(request)
            self._process_response(request, response)

    async def send_request(self, request):
        logger.debug(f"Sending request: {request}")
        logger.debug(f"Protocol used: {self.protocol}")
        if not isinstance(request, self.protocol.Request):
            try:
                _ = self.protocol.Request.model_validate(request)
                logger.debug(f"Request is valid: {_}")
            except Exception as e:
                logger.error(f"Invalid request: {request}")
                raise e

        self.socket.send_json(request)
        response = await self.socket.recv_multipart()

        message = response[0].decode()
        logger.debug(f"Received raw response: {message}")

        return self.protocol.Response.model_validate_json(message)
    
    def _process_response(self, request, response):
        request = self.protocol.Request(**request)
        response = self.protocol.Response(**response)

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
