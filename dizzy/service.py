from pathlib import Path
from typing import Optional

import yaml
import importlib
import logging

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field


logger = logging.getLogger(__name__)


def load_module(path: Path) -> object:
    """Load a module from a path."""
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


class ActionDataclassMixin:
    def __init__(self):
        self.__registered_actions__: dict[str, tuple[str, callable]] = {}

    @property
    def registered_actions(self) -> dict[str, tuple[str, callable]]:
        if not hasattr(self, "__registered_actions__"):
            self.__registered_actions__ = {}

        return self.__registered_actions__

    @registered_actions.setter
    def registered_actions(self, value: tuple[str, callable]):
        self.__registered_actions__ = value

    def register_action(self, name: str, argstr: str, action: callable):
        if not callable(action):
            raise TypeError(f"Action {name} is not callable")

        if name in self.registered_actions:
            # raise ValueError(f"Action {name} already registered")
            # TODO: save a list of actions that were overwritten to check against
            logger.warning(
                f"Action {name} already registered, overwriting: {self.registered_actions[name]}"
            )

        self.registered_actions[name] = (argstr, action)
        logger.debug(f"Registered action {name} with argstr {argstr} for {super()}")

    def get_action(self, name: str) -> tuple[str, callable]:
        return self.registered_actions.get(name, (None, None))

    def try_run_action(self, name: str, *args, **kwargs):
        action = self.get_action(name)[1]
        if callable(action):
            logger.debug(f"Running action {name} for {self.__class__.__name__}")
            return action(*args, **kwargs)
        else:
            return (
                f"Action {name} not found. available actions: {self.possible_actions}"
            )

    @property
    def possible_actions(self) -> list[str]:
        return list(self.registered_actions.keys())


@dataclass
class Task(ABC, ActionDataclassMixin):
    name: Optional[str] = None
    description: Optional[str] = None
    dependencies: Optional[list[str]] = field(default_factory=list)
    requested_actions: Optional[list[str]] = field(default_factory=list)

    def __post_init__(self):
        if self.name is None:
            self.name = self.__class__.__name__

        if self.description is None:
            self.description = self.__class__.__doc__

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


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
                ):
                    logger.debug(f"[{self.name}] Loading task {name} from {task}")
                    obj.name = obj.__name__
                    obj.description = obj.__doc__

                    # This really isn't great, basically when we instantiate a Task, it loses it's default list.
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
            if name in self.tasks:
                raise ValueError(f"Task {name} not loaded")
            raise KeyError(f"Task {name} not found in service {self.name}")
        return self.__loaded_tasks[name]

    def get_tasks(self) -> list[Task]:
        return list(self.__loaded_tasks.values())

    def get_task_names(self) -> list[str]:
        return list(self.__loaded_tasks.keys())


class ServiceManager(ActionDataclassMixin):
    def __init__(self):
        super(ActionDataclassMixin, self).__init__()

        self.services = {}

        logger.debug(f"Created new service manager {self}")

        self.__post_init__()

    def __post_init__(self):
        self.register_action("service_info", "", self.get_services)

    def load_services(self, services: list[Path]):
        for service in services:
            S = Service.load_from_yaml(service)
            self.services[S.name] = S

            # All tasks need to register any actions the service manager offers
            for task in S.get_tasks():
                if hasattr(task, "requested_actions"):
                    for action in task.requested_actions:
                        a = self.get_action(action)
                        if callable(a[1]):
                            task.register_action(action, *a)

        logger.debug(f"SM: Loaded services {self.services}.")

    def find_owner_service(self, task: str) -> Optional[Service]:
        for service in self.services.values():
            if task in service.tasks:
                return service
        return None

    def get_service(self, service: str) -> Optional[Service]:
        if service in self.services:
            return self.services[service]
        return None

    def get_services(self) -> list[Service]:
        return list(self.services.values())

    def get_service_names(self) -> list[str]:
        return list(self.services.keys())

    def get_service_items(self) -> list[tuple[str, list[str]]]:
        return [(s.name, s.get_task_names()) for s in self.services.values()]

    def find_task(self, task: str) -> Optional[Task]:
        owner = self.find_owner_service(task)
        if owner:
            return owner.get_task(task)
        return None

    def resolve_task_dependencies(self, task: str) -> list[Task]:
        """Turn a task into a list of tasks, with dependencies first"""
        t = self.find_task(task)

        if not t or t is None:
            return []

        tasks = []

        if (
            not hasattr(t, "dependencies")
            or t.dependencies is None
            or len(t.dependencies) == 0
        ):
            return [t]

        for dep in t.dependencies:
            tasks = self.resolve_task_dependencies(dep) + tasks
        tasks.append(t)

        return tasks

    def run_tasklist(self, tasklist: list[Task], ctx: dict) -> dict:
        """Run a tasklist in a context"""
        logger.debug(f"Running {tasklist=}")

        results = []
        for task in tasklist:
            logger.debug(f"-- Running task {task.name}, {ctx=}")
            results.append(task.run(ctx))

        logger.debug(f"- Tasklist results: {results=}")
        return results[-1] if len(results) > 0 else None

    def run_task(self, task: str, ctx: dict) -> dict:
        """Run a task in a context"""
        logger.debug(f"Running {task=}")

        tasklist = self.resolve_task_dependencies(task)
        return self.run_tasklist(tasklist, ctx)
