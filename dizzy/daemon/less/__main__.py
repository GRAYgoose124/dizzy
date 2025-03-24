import json
import sys
import logging
from pathlib import Path
from typing import Optional

from ..abstract_protocol import BaseProtocol, DefaultProtocol
from ...entity.manager import EntityManager

logger = logging.getLogger(__name__)


class LocalEntityManager(EntityManager):
    def __init__(self, protocol_dir=None):
        super().__init__()
        self.protocol_dir = protocol_dir
        self.load()
        logger.debug("LocalEntityManager initialized.")
        logger.debug(f"Active entities: {self.entities}")

    def load(self):
        if self.protocol_dir:
            from ..settings import SettingsManager

            settings_manager = SettingsManager(
                write_to_disk=True, live_reload=False, data_root=self.protocol_dir
            )
            settings_manager.load_settings()
            settings = settings_manager.settings
            super().load(settings.common_services, settings.default_entities)
        else:
            super().load([], [])
        logger.debug(f"Activate protocol directory: {self.protocol_dir}")


def handle_request(
    request_data: dict, protocol: BaseProtocol, entity_manager: LocalEntityManager
) -> dict:
    """Handle a single request and return the response."""
    try:
        request = protocol.Request.model_validate(request_data)
        response = protocol.Response.from_request(request)
    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        response = protocol.Response.from_request(None, status="error")
        response.add_error("InvalidRequest", str(e))
        return response.model_dump()

    if request.entity is not None:
        handle_entity_workflow(request, response, entity_manager)
    else:
        response.add_error("BadRequest", "Invalid JSON, no entity or service")

    response.set_status(
        "completed" if len(response.errors) == 0 else "finished_with_errors"
    )
    return response.model_dump()


def handle_entity_workflow(request, response, entity_manager: LocalEntityManager):
    """Handle an entity workflow request."""
    entity = request.entity
    workflow = request.workflow
    step_options = request.step_options

    if not workflow:
        response.add_error("BadWorkflow", "Invalid JSON, no workflow")
        return

    if entity not in entity_manager.entities.keys():
        response.add_error("EntityNotFound", "Entity not found")
        return

    try:
        ctx = entity_manager.run_workflow(workflow, step_options, entity)
    except KeyError as e:
        logger.exception(e)
        response.add_error("KeyError", str(e))
        ctx = {}

    response.ctx = request.ctx
    response.set_result(ctx["workflow"]["result"] if "workflow" in ctx else None)


def argparser():
    import argparse

    parser = argparse.ArgumentParser(description="Process JSON requests from stdin")
    parser.add_argument(
        "--protocol-dir", type=Path, help="Directory containing protocol configuration"
    )
    return parser


def main():
    """Main entry point for the local JSON processor."""
    logging.basicConfig(level=logging.DEBUG)

    args = argparser().parse_args()
    protocol_dir = args.protocol_dir

    # Initialize protocol and entity manager
    if protocol_dir is None:
        logger.debug("Using default protocol")
        protocol = DefaultProtocol()
    else:
        logger.debug(f"Loading protocol from {protocol_dir}")
        protocol = BaseProtocol.load(protocol_dir)

    entity_manager = LocalEntityManager(protocol_dir)

    # Process stdin json object
    request_data = json.load(sys.stdin)
    response_data = handle_request(request_data, protocol, entity_manager)
    print(json.dumps(response_data))


if __name__ == "__main__":
    main()
