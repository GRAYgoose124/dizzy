from dizzy import Task
from dizzy.utils import DependencyError


class C(Task):
    name = "C"
    description = "C task"
    dependencies = ["B"]

    @staticmethod
    def run(ctx):
        ctx["C"] = "C"

        # TODO: lift this out of the Task
        try:
            return f"{ctx['B']}C"
        except KeyError:
            raise DependencyError("Task C depends on B, which was not run")


class D(Task):
    name = "D"
    description = "D task"

    requested_actions = ["entity_info", "service_info"]

    def run(self, ctx):
        ctx["D"] = "D"
        ctx["entity_info"] = self.try_run_action("entity_info")
        ctx["service_info"] = self.try_run_action("service_info")

        print(ctx)
        return "D"
