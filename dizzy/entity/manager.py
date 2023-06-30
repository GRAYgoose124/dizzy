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
    def service_manager(self) -> ServiceManager:
        if self.__common_service_manager is None:
            self.__common_service_manager = ServiceManager()
            logger.debug(f"Created new service manager {self.__common_service_manager}")
        return self.__common_service_manager

    def load_entities(self, entities: list[Path]):
        for entity in entities:
            E = Entity.load_from_yaml(entity)
            self.entities[E.name] = E

            # copy common services from main service manager
            for service in E.services:
                if service in self.service_manager.services:
                    logger.debug(f"Copying service {service} to {E.name}")
                    E.service_manager.services[service] = self.service_manager.services[
                        service
                    ]

            # all tasks need to register any actions the Entity Manager offers
            for service in E.service_manager.services.values():
                for task in service.get_tasks():
                    if hasattr(task, "requested_actions"):
                        for action in task.requested_actions:
                            a = self.get_action(action)
                            if callable(a[1]):
                                task.register_action(action, *a)

        logger.debug(f"Loaded entities {self.entities.keys()}")

    def get_entity(self, entity: str) -> Optional[Entity]:
        if entity in self.entities:
            return self.entities[entity]
        return None

    def find_task(self, task: str) -> Optional[tuple[str, str]]:
        for entity in self.entities.values():
            for service in entity.service_manager.services.values():
                if task in service.tasks:
                    return service.get_task(task)
        return None

    def get_entities(self) -> list[Entity]:
        return list(self.entities.values())

    def get_entity_names(self) -> list[str]:
        return list(self.entities.keys())

    def get_entity_items(self) -> list[tuple[str, list[str]]]:
        return [(e.name, e.services) for e in self.entities.values()]
