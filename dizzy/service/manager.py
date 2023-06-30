import logging
from pathlib import Path
from typing import Optional

from ..task import Task
from . import Service
from ..utils import ActionDataclassMixin

logger = logging.getLogger(__name__)


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
