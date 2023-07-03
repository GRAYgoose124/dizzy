import json
import logging
import zmq

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
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{address}:{port}")

        self.entity_manager = DaemonEntityManager()

    def run(self):
        logger.debug("Server running...")
        while not self.socket.closed:
            try:
                message = self.socket.recv()
            except zmq.error.ContextTerminated:
                break
            self.handle_request(message)

    def stop(self):
        self.socket.close()
        self.context.term()

    def handle_request(self, message):
        logger.debug(f"Received request: {message}")

        response = {
            "status": "incomplete",
            "errors": [],
            "info": [],
            "result": None,
            "ctx": None,
        }

        try:
            request = json.loads(message)
        except json.JSONDecodeError:
            response["errors"].append("Invalid JSON")

        if "entity" in request and request["entity"] is not None:
            self.handle_entity_workflow(request, response)
        elif "service" in request and request["service"] is not None:
            self.handle_service_task(request, response)
        else:
            response["errors"].append("Invalid JSON")

        # out = json.dumps(response).encode()
        if len(response["errors"]) != 0 or "reload" in request and request["reload"]:
            # Try to load entities (and services) again
            self.entity_manager.load()
            response["info"].append("Reloading entities and services...")

        logger.debug(f"Sending response: {response}")
        self.socket.send_json(response)

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
