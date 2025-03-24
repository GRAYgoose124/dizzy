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


def main(protocol_dir: Optional[Path] = None):
    """Main entry point for the local JSON processor."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize protocol and entity manager
    protocol = DefaultProtocol()
    entity_manager = LocalEntityManager(protocol_dir)

    # Process stdin line by line
    for line in sys.stdin:
        try:
            request_data = json.loads(line)
            response_data = handle_request(request_data, protocol, entity_manager)
            print(json.dumps(response_data))
            sys.stdout.flush()  # Ensure output is written immediately
        except json.JSONDecodeError as e:
            error_response = {"status": "error", "errors": {"InvalidJSON": [str(e)]}}
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            logger.exception(e)
            error_response = {
                "status": "error",
                "errors": {"UnexpectedError": [str(e)]},
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process JSON requests from stdin")
    parser.add_argument(
        "--protocol-dir", type=Path, help="Directory containing protocol configuration"
    )
    args = parser.parse_args()
    main(args.protocol_dir)
