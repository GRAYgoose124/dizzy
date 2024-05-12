import logging

from ..task import Task

logger = logging.getLogger(__name__)


class Workflow(list[Task]):
    pass


if __name__ == "__main__":
    pass