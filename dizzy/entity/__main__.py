from dataclasses import dataclass, asdict
import logging
from pathlib import Path

import yaml

from ..service import ServiceManager
from ..utils import ActionDataclassMixin

logger = logging.getLogger(__name__)


@dataclass
class Entity(ActionDataclassMixin):
    """Base class for all entities.

    An entity is... A decoupled set of services and workflows that can be deployed.
    """

    name: str
    description: str
    services: list[str]
    workflows: list[str]

    def __post_init__(self):
        self.__services_root = None
        self.__service_manager = None

    @staticmethod
    def load_from_yaml(entity: Path) -> "Entity":
        with open(entity) as f:
            logger.debug(f"Loading entity from {entity}")
            E = Entity(**yaml.safe_load(f)["entity"])
            E.__services_root = entity.parent / "services"

            E.service_manager.load_services(E.get_service_files())

            # All tasks need to register any actions the Entity offers
            for service in E.service_manager.services.values():
                for task in service.get_tasks():
                    if hasattr(task, "requested_actions"):
                        for action in task.requested_actions:
                            a = E.get_action(action)
                            if callable(a[1]):
                                task.register_action(action, *a)

            logger.debug(f"Loaded entity {E.name}")
            return E

    def save_to_yaml(self, entity: Path = None):
        if entity is None:
            if self.__services_root is None:
                raise ValueError("No services root set, cannot save entity.")
            entity = self.__services_root.parent / "entity.yml"
        else:
            self.__services_root = entity.parent / "services"

        with open(entity, "w") as f:
            yaml.safe_dump({"entity": asdict(self)}, f)

    @property
    def service_manager(self) -> ServiceManager:
        if self.__service_manager is None:
            self.__service_manager = ServiceManager()
        return self.__service_manager

    def get_service_files(self) -> list[Path]:
        if self.__services_root is None:
            raise ValueError("No services root set")

        service_files = self.__services_root.glob(f"**/*.yml")
        service_files = [
            f
            for f in service_files
            if f.parent.name in self.services or self.services == ["*"]
        ]

        logger.debug(
            f"Found {self.name} service files {service_files} in {self.__services_root}"
        )

        return service_files

    def run_workflow(self, workflow: str):
        """A workflow is a set of non-dependent tasks made dependent by the workflow."""
        logger.debug(f"Running workflow {workflow} for entity {self.name}")

        ctx = {"workflow": {"input": {}, "result": {}}}
        # parse workflow
        wf = self.workflows[workflow]
        tasks = wf.replace(" ", "").split("->")

        for i, task in enumerate(tasks):
            if tasks[i - 1] in ctx["workflow"]["result"]:
                ctx["workflow"]["input"][task] = ctx["workflow"]["result"][tasks[i - 1]]

            ctx["workflow"]["result"][task] = self.service_manager.run_task(task, ctx)

        return ctx
