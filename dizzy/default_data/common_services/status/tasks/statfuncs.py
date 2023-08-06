import logging
from dizzy import Task

logger = logging.getLogger(__name__)


class Tasky(Task):
    """A task"""

    @staticmethod
    def run():
        return "Task"


class Info(Task):
    """Gets info about loaded services."""

    requested_actions = ["entity_info", "service_info"]

    def run(self):
        info = {}
        try:
            logger.debug(f"Trying to get service info from %s", self)
            info["service"] = self.try_run_action("service_info")
            info["entity"] = self.try_run_action("entity_info")
        except Exception as e:
            logger.error(f"Error getting entity info: {e}")
            info["error"] = f"{e}"

        return info
