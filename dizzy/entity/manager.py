import logging
from pathlib import Path
from typing import Optional

from . import Entity
from ..service import ServiceManager
from ..utils import ActionDataclassMixin

logger = logging.getLogger(__name__)


class EntityManager(ActionDataclassMixin):
    def __init__(self, service_manager: ServiceManager = None):
        super(ActionDataclassMixin, self).__init__()

        self.entities = {}
        self.__common_service_manager = service_manager or ServiceManager()

        logger.debug(f"Created new entity manager {self}")

        self.__post_init__()

    def __post_init__(self):
        self.register_action("entity_info", "", self.get_entities)

    @property
    def csm(self) -> ServiceManager:
        return self.common_service_manager

    @property
    def common_service_manager(self) -> ServiceManager:
        if self.__common_service_manager is None:
            self.__common_service_manager = ServiceManager()
            logger.debug(f"Created new service manager {self.__common_service_manager}")
        return self.__common_service_manager

    def reset(self):
        self.entities = {}
        self.common_service_manager.reset()

    def load(self, services: dict, entities: dict):
        self.csm.load_services(services.values())
        # now register actions for the common service manager's tasks
        # TODO: all location of tasks need to check common services too.
        for service in self.csm.services.values():
            for task in service.get_tasks():
                if hasattr(task, "requested_actions"):
                    for action in task.requested_actions:
                        a = self.get_action(action)
                        if callable(a[1]):
                            task.register_action(action, *a)

        self.load_entities(entities.values())

    def _copy_common_services(self, entity: Entity):
        for service in entity.services:
            if service in self.common_service_manager.services:
                logger.debug(f"Copying service {service} to {entity.name}")
                entity.service_manager.services[service] = (
                    self.common_service_manager.services[service]
                )

    def _register_task_actions(self, entity: Entity):
        for service in entity.service_manager.services.values():
            for task in service.get_tasks():
                if hasattr(task, "requested_actions"):
                    for action in task.requested_actions:
                        a = entity.get_action(action)
                        if callable(a[1]):
                            task.register_action(action, *a)

    def load_entities(self, entity_paths: list[Path]):
        for entity in entity_paths:
            E = Entity.load_from_yaml(entity)
            self.entities[E.name] = E

            self._copy_common_services(E)
            self._register_task_actions(E)

        logger.debug(f"Loaded entities {self.entities.keys()}")

    def get_workflows(self) -> list[tuple[str, str]]:
        workflows = []
        for entity in self.entities.values():
            for workflow in entity.workflows:
                workflows.append((entity.name, workflow))

        return workflows

    def run_workflow(
        self, workflow: str, step_options: dict = None, entity_name: str = None
    ):
        if entity_name in self.entities:
            return self.get_entity(entity_name).run_workflow(workflow, step_options)
        else:
            logger.info(f"Entity={entity_name} not found. Searching for {workflow} in all entities.")
            for e, wf in self.get_workflows():
                if wf == workflow:
                    return self.get_entity(e).run_workflow(workflow, step_options)
            logger.warning(f"Workflow={workflow} not found in any entity.")
    
    def get_entity(self, entity: str) -> Optional[Entity]:
        if entity in self.entities:
            return self.entities[entity]
        else:
            logger.warning(f"Entity {entity} not found.")
            return None

    def find_task(self, task: str) -> Optional[tuple[str, str]]:
        for entity in self.entities.values():
            for service in entity.service_manager.services.values():
                if task in service.tasks:
                    return service.get_task(task)
                
        logger.warning(f"Task={task} not found in any entity.")
        return None

    def find_service(self, service: str) -> Optional[tuple[str, str]]:
        for entity in self.entities.values():
            if service in entity.service_manager.services:
                return entity.service_manager.get_service(service)
        
        logger.warning(f"Service={service} not found in any entity.")
        return None

    def find_owner_entity(self, task: str) -> Optional[Entity]:
        for entity in self.entities.values():
            for service in entity.service_manager.services.values():
                if task in service.tasks:
                    return entity
        
        logger.warning(f"Owner entity for task={task} not found in any entity.")
        return None

    def find_owner_service(self, task: str) -> Optional[tuple[str, str]]:
        for entity in self.entities.values():
            for service in entity.service_manager.services.values():
                if task in service.tasks:
                    return entity.service_manager.get_service(service)
        
        logger.warning(f"Owner service for task={task} not found in any entity.")
        return None

    def get_entities(self) -> list[Entity]:
        return list(self.entities.values())

    def get_entity_names(self) -> list[str]:
        return list(self.entities.keys())

    def __getitem__(self, entity: str) -> Entity:
        return self.get_entity(entity)
