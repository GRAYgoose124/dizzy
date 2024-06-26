from dataclasses import dataclass, field
import os
from pathlib import Path
from uuid import uuid4

from dizzy import Task
from dizzy.daemon.settings import SettingsManager

SM = SettingsManager()

data_root = SM.settings.data_root

PROJECT_ROOT = data_root.parent / "projects"


@dataclass
class Project:
    id: str = field(default=uuid4().hex)
    name: str = "New Project"
    description: str = "A new project"
    root: str = ""
    paths: list[dict] = field(default_factory=list)
    files: list[dict] = field(default_factory=list)

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

    # TODO: add extra_contexts to Task specifically
    # extra_context = ["project"]

    # would need to copy or unify ProjectTasks... :x
    # project: Project = field(default_factory=Project)

    def add_to_context(self, ctx):
        ctx["project"] = self.project.to_dict()
        return ctx

    @classmethod
    def load_from_context(cls, ctx):
        cls.project = Project(**ctx["project"])
        return cls


class CreateProject(ProjectTask):
    """Create a project directory with a given UUID"""

    @staticmethod
    def run(ctx):
        ctx["project"] = Project()
        path = PROJECT_ROOT / ctx["project"].id
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path


class ListProjects(ProjectTask):
    """List all projects in the project directory"""

    @staticmethod
    def run(ctx):
        project_ids = [p.name for p in PROJECT_ROOT.iterdir() if p.is_dir()]
        ctx["project_ids"] = project_ids
        return project_ids


class ReadProjectFiles(ProjectTask):
    """Read a file from the project of a given UUID"""

    dependencies = ["CreateProject"]

    @staticmethod
    def run(ctx):
        files = []
        for file in ctx["project"].paths:
            path: Path = PROJECT_ROOT / ctx["project"].id / file["path"]
            with open(path, "r") as f:
                content = f.read()
            files.append({"path": file["path"], "content": content})
        ctx["project"].files = files
        return files


class WriteProjectFiles(ProjectTask):
    """Write a file to the project of a given UUID"""

    dependencies = ["CreateProject"]

    @staticmethod
    def run(ctx):
        for file in ctx["project"].files:
            path: Path = PROJECT_ROOT / ctx["project"].id / file["path"]
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as f:
                f.write(file["content"])


# Runs on server, but requested by client, client must have the file, we will open a new connection to the client
class UploadProjectFiles(Task):
    pass
