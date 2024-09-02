from pathlib import Path
from typing import Optional

import yaml
import logging

from dataclasses import asdict, dataclass, field


logger = logging.getLogger(__name__)


from ..utils import load_module, ActionDataclassMixin
from ..task import Task


@dataclass
class Service(ActionDataclassMixin):
    name: str
    description: str

    tasks: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.__task_root = None
        self.__loaded_tasks = {}

    def _load_tasks(self):
        for task in Path(self.__task_root).glob("*.py"):
            module = load_module(task)
            for name, obj in module.__dict__.items():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, Task)
                    and name in self.tasks
                    or self.tasks == ["*"]
                ):
                    logger.debug(f"[{self.name}] Loading task {name} from {task}")
                    obj.name = obj.__name__
                    obj.description = obj.__doc__

                    # This really isn't great, basically when we instantiate a Task, it loses it's default lists.
                    dependencies = None
                    if hasattr(obj, "dependencies"):
                        dependencies = obj.dependencies.copy()
                    requested_actions = None
                    if hasattr(obj, "requested_actions"):
                        requested_actions = obj.requested_actions.copy()

                    obj = obj()

                    if dependencies is not None:
                        setattr(obj, "dependencies", dependencies)
                    if requested_actions is not None:
                        setattr(obj, "requested_actions", requested_actions)

                    if hasattr(obj, "requested_actions"):
                        for action in obj.requested_actions:
                            a = self.get_action(action)
                            if callable(a[1]):
                                obj.register_action(action, *a)

                    self.__loaded_tasks[name] = obj

    @staticmethod
    def load_from_yaml(service: Path) -> "Service":
        with open(service) as f:
            logger.debug(f"Loading service from {service}")
            S = Service(**yaml.safe_load(f)["service"])
            S.__task_root = str(service.parent / "tasks")
            S._load_tasks()

            logger.debug(f"Loaded service {S.name} with tasks {S.tasks}")
            return S

    def save_to_yaml(self, service: Path = None):
        if service is None:
            if self.__task_root is None:
                raise ValueError("No services root set, cannot save entity.")
            service = self.__task_root.parent / "service.yml"
        else:
            self.__task_root = service.parent / "tasks"

        with open(service, "w") as f:
            yaml.safe_dump({"service": asdict(self)}, f)

    def get_task(self, name: str) -> Task:
        if name not in self.__loaded_tasks:
            logger.error(f"Task {name} not loaded")
            if name in self.tasks:
                raise ValueError(f"Task {name} not loaded")
            raise KeyError(f"Task {name} not found in service {self.name}")
        return self.__loaded_tasks[name]

    def get_tasks(self) -> list[Task]:
        return list(self.__loaded_tasks.values())

    def get_task_names(self) -> list[str]:
        return list(self.__loaded_tasks.keys())
