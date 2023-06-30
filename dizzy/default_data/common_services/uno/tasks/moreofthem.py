from dizzy import Task


class C(Task):
    name = "C"
    description = "C task"
    dependencies = ["B"]

    @staticmethod
    def run(ctx):
        ctx["C"] = "C"
        return f"{ctx['B']}C"


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
