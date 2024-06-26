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

    def _register_task_actions(self, task: Task):
        if hasattr(task, "requested_actions"):
            for action in task.requested_actions:
                a = self.get_action(action)
                if callable(a[1]):
                    task.register_action(action, *a)

    def load_services(self, services: list[Path]):
        for service in services:
            if not service.exists():
                logger.error(f"Service file {service} does not exist.")
                continue

            S = Service.load_from_yaml(service)
            self.services[S.name] = S

            # All tasks need to register any actions the service manager offers
            for task in S.get_tasks():
                self._register_task_actions(task)

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

    def get_all_known_tasks(self):
        """Get all known tasks from all services"""
        tasks = []
        for service in self.services.values():
            tasks += service.get_tasks()
        return tasks

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
            if dep == task:
                continue
            tasks = self.resolve_task_dependencies(dep) + tasks
        tasks.append(t)

        return tasks

    def run_tasklist(
        self, tasklist: list[Task], args: dict = None, ctx: dict = None
    ) -> dict:
        """Run a tasklist in a context"""
        logger.debug(f"Running {tasklist=}")

        ctx = ctx or {}
        for task in tasklist:
            this_tasks_args = {dep: ctx[dep].pop() for dep in task.dependencies}
            if args is not None:
                this_tasks_args.update(args)

            logger.debug(f"-- Running task {task.name}, {ctx=}")
            result = task.run(this_tasks_args)

            ctx.setdefault(task.name, []).append(result)

        try:
            final = ctx[tasklist[-1].name].pop()
        except IndexError:
            final = None
            logger.error(
                f"Tasklist was empty, {tasklist=}, {ctx=} - did you define the requested Task?"
            )
        logger.debug(f"Tasklist {final=}, {ctx=} (should be empty)")
        return final

    def run_task(self, task: str, args: dict = None, ctx: dict = None) -> dict:
        """Run a task in a context"""
        logger.debug(f"Running {task=}")

        tasklist = self.resolve_task_dependencies(task)
        return self.run_tasklist(tasklist, args, ctx)
