from dizzy import Task


class A(Task):
    description = "A task"

    @staticmethod
    def run():
        return "A"


class B(Task):
    description = "B task"
    dependencies = ["A"]

    @staticmethod
    def run(A):
        return f"{A}B"
