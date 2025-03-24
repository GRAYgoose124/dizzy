import asyncio
import json
import logging
import uuid
import importlib
import zmq
import zmq.asyncio
from pathlib import Path
from dizzy import EntityManager
from ..abstract_protocol import BaseProtocol, DefaultProtocol
from ..settings import SettingsManager

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
    def __init__(
        self,
        protocol: BaseProtocol = DefaultProtocol,
        address="*",
        port=5555,
        protocol_dir=None,
    ):
        self._check_and_load_protocol(protocol, protocol_dir)

        self.context = zmq.asyncio.Context()
        self.frontend = self.context.socket(zmq.ROUTER)

        try:
            self.frontend.bind(f"tcp://{address}:{port}")
        except zmq.error.ZMQError as e:
            logger.error(f"Error binding to {address}:{port}: {e}")
            raise RuntimeError(f"Error binding to {address}:{port}: {e}")

        self.entity_manager = DaemonEntityManager(protocol_dir)

        self.clients = {}

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
            except KeyboardInterrupt:
                logger.debug("Server stopped.")
                break
            except Exception as e:
                logger.exception(e)
                continue

            logger.debug("About to handle request...")
            await self.handle_request(identity, message)

    def stop(self):
        self.frontend.close()
        self.context.term()
        self.running = False

    def _generate_uuid(self):
        return uuid.uuid4().hex

    async def handle_request(self, identity: str, message: bytes):
        logger.debug(f"Received request: {message}")
        if identity not in self.clients:
            self.clients[identity] = {
                "uuid": uuid.uuid4().hex,
                "transactions": [],
                "transaction_uuids": [],
            }
        this_client = self.clients[identity]["uuid"]

        response = None
        try:
            request = self.protocol.Request.model_validate_json(message.decode())
            request.id = self._generate_uuid()
            request.requester = this_client
            response = self.protocol.Response.from_request(request)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            response = self.protocol.Response.from_request(this_client, status="error")
            request = None
            logger.debug(f"Invalid JSON: {message}")
            response.add_error("InvalidJSON", "Invalid JSON: " + str(e))
        except TypeError as e:
            response = self.protocol.Response.from_request(this_client, status="error")
            request = None
            logger.debug(f"Invalid request: {e}")
            response.add_error("InvalidRequest", "Invalid request: " + str(e))

        self.clients[identity]["transactions"].append((request, response))
        self.clients[identity]["transaction_uuids"].append(request.id)

        unhandled = True
        if request.entity is not None:
            self.handle_entity_workflow(request, response)
            unhandled = False

        if unhandled:
            response.add_error("BadRequest", "Invalid JSON, no entity or service")

        response.set_status(
            "completed" if len(response.errors) == 0 else "finished_with_errors"
        )

        try:
            logger.debug(f"Response: {response}")
            response_data = response.model_dump_json().encode()
        except Exception as e:
            logger.error(f"Error serializing response: {e}")
            response.add_error("SerializationError", str(e))
            response_data = response.model_dump_json().encode()

        logger.debug(
            f"\n\n{request.model_dump_json(indent=2)}\n\nreturned\n\n{response.model_dump_json(indent=2)}\n"
        )
        await self.frontend.send_multipart([identity, b"", response_data])

    def handle_entity_workflow(self, request, response):
        entity = request.entity
        workflow = request.workflow
        step_options = request.step_options

        if not workflow:
            response.add_error("BadWorkflow", "Invalid JSON, no workflow")
            return

        if entity not in self.entity_manager.entities.keys():
            response.add_error("EntityNotFound", "Entity not found")
            return

        try:
            ctx = self.entity_manager.run_workflow(workflow, step_options, entity)
        except KeyError as e:
            logger.exception(e)
            response.add_error("KeyError", str(e))
            ctx = {}

        response.ctx = request.ctx

        response.set_result(ctx["workflow"]["result"] if "workflow" in ctx else None)

    def handle_service_task(self, request, response):
        service = request.service
        task = request.task
        ctx = request.ctx

        if not task:
            response.add_error("BadTask", "Invalid JSON, no task")
            return

        if service not in self.entity_manager.common_service_manager.services:
            response.add_error("ServiceNotFound", "Service not found")
            return

        response.add_info(
            "available_services",
            (
                service,
                self.entity_manager.common_service_manager.get_service(
                    service
                ).get_task_names(),
            ),
        )

        try:
            response.result = self.entity_manager.common_service_manager.run_task(
                task, ctx
            )
            response.ctx = ctx
        except Exception as e:
            response.add_error("FinalError", f"Error running task: {e}")

    def handle_query(self, request, response):
        """"""
        pass

    def _check_and_load_protocol(self, protocol: BaseProtocol, protocol_dir: Path):
        self.protocol_dir = protocol_dir

        if protocol_dir is not None:
            logger.debug(f"Loading protocol from {protocol_dir}")
            self.protocol = BaseProtocol.load(protocol_dir)
        else:
            logger.debug(f"Using default protocol")
            self.protocol = protocol

        if isinstance(protocol, type):
            self.protocol = protocol()

        assert isinstance(
            self.protocol, BaseProtocol
        ), f"Protocol must be a subclass of BaseProtocol, got {type(self.protocol)}"
