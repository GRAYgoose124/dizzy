import importlib.util
import logging
from pathlib import Path

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
