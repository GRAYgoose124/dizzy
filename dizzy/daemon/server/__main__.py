import asyncio
import json
import logging
import uuid
import zmq
import zmq.asyncio

from dizzy import EntityManager
from ..settings import SettingsManager
from ..protocol import Response, Request

logger = logging.getLogger(__name__)


class DaemonEntityManager(EntityManager):
    def __init__(self, protocol_dir=None):
        super().__init__()

        self.protocol_dir = protocol_dir
        self.settings_manager = SettingsManager(
            write_to_disk=True, live_reload=False, data_root=self.protocol_dir
        )
        self.load()
        logger.debug("DaemonEntityManager initialized.")
        logger.debug(f"Active entities: {self.entities}")

    def load(self):
        self.settings_manager.load_settings()
        settings = self.settings_manager.settings
        super().load(settings.common_services, settings.default_entities)
        logger.debug(f"Activate protocol directory: {self.protocol_dir}")


class SimpleRequestServer:
    def __init__(self, address="*", port=5555, protocol_dir=None):
        self.context = zmq.asyncio.Context()
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(f"tcp://{address}:{port}")

        self.entity_manager = DaemonEntityManager(protocol_dir)

    async def run(self):
        logger.debug("Server running...")

        self.running = True
        while self.running != False:
            if self.frontend.closed:
                break

            try:
                [identity, _, message] = await self.frontend.recv_multipart()
            except (zmq.error.ZMQError, asyncio.exceptions.CancelledError):
                logger.debug("Server stopped.")
                break

            logger.debug("About to handle request...")
            await self.handle_request(identity, message)

    def stop(self):
        self.frontend.close()
        self.context.term()
        self.running = False

    async def handle_request(self, identity: str, message: bytes):
        logger.debug(f"Received request: {message}")

        try:
            request = Request(**json.loads(message.decode()))
            response = Response.from_request(identity, request)
            logger.debug(f"\n{request}\n\nreturned\n\n{response}\n")

        except (json.JSONDecodeError, UnicodeDecodeError):
            response = Response.from_request(identity, None)
            request = None
            logger.debug(f"Invalid JSON: {message}")

        unhandled = True
        if request.entity is not None:
            self.handle_entity_workflow(request, response)
            unhandled = False
        if request.service is not None:
            self.handle_service_task(request, response)
            unhandled = False

        if unhandled:
            response.add_error("BadRequest", "Invalid JSON, no entity or service")

        response_data = response.to_json().encode()
        await self.frontend.send_multipart([identity, b"", response_data])

    def handle_entity_workflow(self, request, response):
        entity = request.entity
        workflow = request.workflow

        if not workflow:
            response.add_error("BadWorkflow", "Invalid JSON, no workflow")
            return

        if entity not in self.entity_manager.entities.keys():
            response.add_error("EntityNotFound", "Entity not found")
            return

        try:
            ctx = self.entity_manager[entity].run_workflow(workflow)
        except KeyError as e:
            response.add_error("KeyError", str(e))
            ctx = None

        response.ctx = request.ctx

        response.set_status(
            "completed" if len(response.errors) == 0 else "finished_with_errors"
        )
        response.set_result(ctx["workflow"]["result"] if "workflow" in ctx else None)

    def handle_service_task(self, request, response):
        service = request.service
        task = request.task
        ctx = request.ctx

        if not task:
            response.add_error("BadTask", "Invalid JSON, no task")
            return

        if service not in self.entity_manager.service_manager.services:
            response.add_error("ServiceNotFound", "Service not found")
            return

        response.add_info(
            "available_services",
            (
                service,
                self.entity_manager.service_manager.get_service(
                    service
                ).get_task_names(),
            ),
        )

        try:
            response.result = self.entity_manager.service_manager.run_task(task, ctx)
            response.ctx = ctx
        except Exception as e:
            response.add_error("FinalError", f"Error running task: {e}")

        response.set_status(
            "completed" if len(response.errors) == 0 else "finished_with_errors"
        )

    def handle_query(self, request, response):
        """"""
        pass
