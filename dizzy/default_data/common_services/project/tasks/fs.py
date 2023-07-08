import os
from pathlib import Path

from dizzy import Task
from dizzy.daemon.settings import data_root


class ReadProjectFile(Task):
    """Read a file from the project of a given UUID"""

    @staticmethod
    def run(ctx):
        path: Path = data_root / "projects" / ctx["project"]["id"] / ctx["filepath"]

        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} not found")

        with open(path, "r") as f:
            ctx["content"] = f.read()

        return ctx["content"]


class WriteProjectFile(Task):
    """Write a file to the project of a given UUID"""

    @staticmethod
    def run(ctx):
        path: Path = data_root / "projects" / ctx["project"]["id"] / ctx["filepath"]

        if not path.is_file():
            raise TypeError(f"Path {path} is not a file")

        if not os.path.exists(path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

        with open(path, "w") as f:
            f.write(ctx["content"])

        return ctx["content"]
