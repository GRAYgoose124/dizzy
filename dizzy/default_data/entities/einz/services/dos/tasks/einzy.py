from dizzy import Task


class EinzyA(Task):
    """A task"""

    @staticmethod
    def run(ctx):
        ctx["EinzyA"] = "A"
        return "EinzyA"


class EinzyB(Task):
    """B task"""

    dependencies = ["EinzyA"]

    @staticmethod
    def run(ctx):
        ctx["B"] = f"{ctx['EinzyA']}B"
        return f"{ctx['EinzyA']}B"


class EinzInfo(Task):
    """Gets info about loaded services."""

    dependencies = ["Info"]

    def run(self, ctx):
        ctx["EinzInfo"] = f"{ctx['Info']}"

        return ctx["EinzInfo"]


class NotUsed(Task):
    """Ignored"""

    @staticmethod
    def run(ctx):
        return "Not used"
