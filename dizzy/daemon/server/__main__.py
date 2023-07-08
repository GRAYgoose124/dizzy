import asyncio
import json
import logging
import uuid
import zmq
import zmq.asyncio

from dizzy import EntityManager
from ..settings import SettingsManager


logger = logging.getLogger(__name__)


class DaemonEntityManager(EntityManager):
    def __init__(self):
        super().__init__()

        self.settings_manager = SettingsManager(write_to_disk=True)
        self.load()

    def load(self):
        self.settings_manager.load_settings()
        settings = self.settings_manager.settings
        super().load(settings.common_services, settings.default_entities)

        logger.debug("DaemonEntityManager initialized.")


class SimpleRequestServer:
    def __init__(self, address="*", port=5555):
        self.context = zmq.asyncio.Context()
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(f"tcp://{address}:{port}")

        self.entity_manager = DaemonEntityManager()

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

            await self.handle_request(identity, message)

    def stop(self):
        self.frontend.close()
        self.context.term()
        self.running = False

    async def handle_request(self, identity, message):
        logger.debug(f"Received request: {message}")

        response = {
            "id": uuid.uuid4().hex,
            "status": "incomplete",
            "errors": [],
            "info": [],
            "result": None,
            "request": message.decode(),
            "ctx": None,
        }

        try:
            request = json.loads(message)
        except (json.JSONDecodeError, UnicodeDecodeError):
            response["errors"].append("Invalid JSON")
            request = {}

        if "id" in request:
            response["id"] = request["id"]

        if "entity" in request and request["entity"] is not None:
            self.handle_entity_workflow(request, response)
        elif "service" in request and request["service"] is not None:
            self.handle_service_task(request, response)
        else:
            response["errors"].append("Invalid JSON")

        if len(response["errors"]) != 0 or ("reload" in request and request["reload"]):
            self.entity_manager.load()
            response["info"].append("Reloading entities and services...")

        response_data = json.dumps(response).encode("utf-8")
        await self.frontend.send_multipart([identity, b"", response_data])

    def handle_entity_workflow(self, request, response):
        entity = request["entity"]
        workflow = request.get("workflow", None)

        if not workflow:
            response["errors"].append("Invalid JSON, no workflow")
            return

        if entity not in self.entity_manager.entities.keys():
            response["errors"].append("Entity not found")
            return

        response["entity"] = entity
        try:
            ctx = self.entity_manager.get_entity(entity).run_workflow(workflow)
        except KeyError as e:
            response["errors"].append(f"No such workflow: {e}")
            ctx = None

        # response["ctx"] = ctx
        response["ctx"] = request.get("ctx", {})

        # set
        response["workflow"] = request["workflow"]
        response["status"] = (
            "completed" if len(response["errors"]) == 0 else "finished_with_errors"
        )
        response["result"] = ctx["workflow"]["result"] if ctx else None

    def handle_service_task(self, request, response):
        service = request["service"]
        task = request.get("task", None)

        if not task:
            response["errors"].append("Invalid JSON, no task")
            return

        if service not in self.entity_manager.service_manager.services:
            response["errors"].append("Service not found")
            return

        response["available_services"] = (
            service,
            self.entity_manager.service_manager.get_service(service).get_task_names(),
        )

        ctx = request.get("ctx", {})

        try:
            result = self.entity_manager.service_manager.run_task(task, ctx)
            response["result"] = result
            response["ctx"] = ctx
            response["status"] = (
                "completed" if len(response["errors"]) == 0 else "finished_with_errors"
            )
        except Exception as e:
            response["errors"].append(f"Error running task: {e}")

    def handle_query(self, request, response):
        """"""
        pass
