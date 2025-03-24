class IOCoupler:
    """Interfaces two tasks by routing their IO signals as context data"""

    def __init__(self, task1: Task, task2: Task):
        self.task1 = task1
        self.task2 = task2

    def run(self, ctx: dict):
        ctx = self.task1.run(ctx)
        return self.task2.run(ctx)
