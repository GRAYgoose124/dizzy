import pytest
from pathlib import Path

from dizzy import ServiceManager, Service
from dizzy.daemon.settings import common_services


class TestServiceManager:
    def setup_method(self):
        self.man = ServiceManager()
        self.man.load_services(common_services.values())

        print(common_services, self.man.services.values())

    def test_ServiceManager(self):
        assert self.man.get_service("uno").get_task("D").run({}) == "D"

    def test_task_resolution(self):
        assert [t.name for t in self.man.resolve_task_dependencies("D")] == ["D"]

    def test_task_resolution_with_dependencies(self):
        assert [t.name for t in self.man.resolve_task_dependencies("C")] == [
            "A",
            "B",
            "C",
        ]

    def test_run_tasklist(self):
        ctx = {}
        tasklist = self.man.resolve_task_dependencies("C")
        self.man.run_tasklist(tasklist, ctx)
        assert ctx == {"A": "A", "B": "AB", "C": "C"}

    def test_requested_actions(self):
        self.man.possible_actions == ["service_info"]

    def test_run_action(self):
        result = self.man.try_run_action("service_info")
        assert len(result) == 3  # project, status, uno


class TestService:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.service = Service.load_from_yaml(common_services["uno"])

    def teardown_method(self):
        self.test_path.unlink()

    def test_Service_dump(self):
        self.service.save_to_yaml(self.test_path)

        test_S = Service.load_from_yaml(self.test_path)
        assert self.test_path.exists()
        assert test_S.name == "uno"
        assert not hasattr(test_S, "__task_root")

    def test_requested_actions(self):
        assert self.service.get_task("D").requested_actions == [
            "entity_info",
            "service_info",
        ]
        ctx = {}

        self.service.get_task("D").run(ctx)

        assert "entity_info" in ctx  # Not runnable by services only.
        assert "service_info" in ctx
