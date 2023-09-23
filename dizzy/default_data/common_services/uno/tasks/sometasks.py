from dizzy import Task


class A(Task):
    description = "A task"

    @staticmethod
    def run(ctx):
        return "A"


class B(Task):
    description = "B task"
    dependencies = ["A"]

    @staticmethod
    def run(ctx):
        return f"{ctx['A']}B"
