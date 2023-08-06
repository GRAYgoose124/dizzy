from dizzy import Task
from dizzy.utils import DependencyError


class C(Task):
    name = "C"
    description = "C task"
    dependencies = ["B"]

    @staticmethod
    def run(B):
        return f"{B}C"


class D(Task):
    name = "D"
    description = "D task"

    requested_actions = ["entity_info", "service_info"]

    def run(self):
        result = {}
        result["final"] = "D"
        result["entity_info"] = self.try_run_action("entity_info")
        result["service_info"] = self.try_run_action("service_info")

        return result
