from dizzy import Task


class Inspect(Task):
    """Ignored"""

    @staticmethod
    def run(ctx):
        return "Inspect"
        # return ctx
