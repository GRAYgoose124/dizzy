from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Optional

from .utils import ActionDataclassMixin


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
