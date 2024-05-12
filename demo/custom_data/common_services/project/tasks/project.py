from dataclasses import dataclass, field
import os
from pathlib import Path

from dizzy import Task
from dizzy.daemon.settings import data_root

PROJECT_ROOT = data_root.parent / "projects"


@dataclass
class Project:
    id: str
    name: str
    description: str
    root: str

    def __post_init__(self):
        self.root = PROJECT_ROOT / self.id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "root": self.root,
        }


class ProjectTask(Task):
    """Base class for tasks that interact with data"""

    project: Project

    def add_to_context(self, ctx):
        ctx["project"] = self.project.to_dict()
        return ctx

    @classmethod
    def load_from_context(cls, ctx):
        cls.project = Project(**ctx["project"])
        return cls


class CreateProjectDir(Task):
    """Create a project directory with a given UUID"""

    @staticmethod
    def run(ctx):
        path: Path = PROJECT_ROOT / ctx["project"]["id"]
        path.mkdir(parents=True, exist_ok=True)
        return {"status": "success" if path.exists() else "failed", "path": path}


class SetProjectDir(Task):
    """Get the project directory of a given UUID"""

    requested_actions = ["set_project_dir"]

    @staticmethod
    def run(ctx):
        ctx["project"] = Project(**ctx["
        ctx["project"]["root"] = PROJECT_ROOT / ctx["project"]["id"]
        return ctx["project"]["root"]


class ReadProjectFiles(Task):
    """Read a file from the project of a given UUID"""

    @staticmethod
    def run(ctx):
        path: Path = PROJECT_ROOT / ctx["project"]["id"] / ctx["filepath"]

        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} not found")

        with open(path, "r") as f:
            ctx["content"] = f.read()

        return ctx["content"]


class WriteProjectFiles(Task):
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
