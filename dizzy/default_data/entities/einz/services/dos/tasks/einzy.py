from dizzy import Task


class EinzyA(Task):
    """A task"""

    @staticmethod
    def run():
        return "A"


class EinzyB(Task):
    """B task"""

    dependencies = ["EinzyA"]

    @staticmethod
    def run(EinzyA):
        return f"{EinzyA}B"


class EinzInfo(Task):
    """Gets info about loaded services."""

    dependencies = ["Info"]

    @staticmethod
    def run(Info):
        return f"Einz:{Info}"


class NotUsed(Task):
    """Ignored"""

    @staticmethod
    def run():
        return "Not used"
