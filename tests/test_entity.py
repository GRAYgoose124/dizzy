from pathlib import Path
from dizzy import Entity, EntityManager
from dizzy.daemon import all_entities, DaemonEntityManager


class TestEntity:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.entity = Entity.load_from_yaml(all_entities["einz"])

    def teardown_method(self):
        self.test_path.unlink()

    def test_Entity_dump(self):
        self.entity.save_to_yaml(self.test_path)
        test_E = Entity.load_from_yaml(self.test_path)

        assert self.test_path.exists()
        assert test_E.name == "einz"
        assert not hasattr(test_E, "__services_root")


class TestEntityManager:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.em = EntityManager()

        self.em.load_entities(all_entities.values())

    def teardown_method(self):
        self.test_path.unlink()

    def test_requested_actions(self):
        assert self.em.possible_actions == ["entity_info"]


class TestDaemonEntityManager:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.em = DaemonEntityManager()

        self.em.load_entities(all_entities.values())

    def teardown_method(self):
        self.test_path.unlink()

    def test_requested_actions(self):
        # assert self.em.service_manager.find_task("D").possible_actions in [
        #     "entity_info",
        #     "service_info",
        # ]i
        D = self.em.find_task("D")
        assert all(
            action in D.possible_actions for action in ["entity_info", "service_info"]
        )

        ctx = {}

        result = D.run(ctx)

        print(result, ctx)
