from pathlib import Path
from dizzy import Entity, EntityManager
from dizzy.daemon import all_entities, DaemonEntityManager


class TestWorkflow:
    def setup_method(self):
        self.test_path = Path("test.yaml")
        self.test_path.touch()

        self.em = DaemonEntityManager()

        self.em.load_entities(all_entities.values())

    def teardown_method(self):
        self.test_path.unlink()

    def test_workflow(self):
        workflows = self.em.get_workflows()
        workflow_names = [w[1] for w in workflows]
        assert workflow_names == ["love", "einzy", "info", "hubris"]
        workflow_entities = [w[0] for w in workflows]
        assert workflow_entities == ["zwei", "einz", "einz", "drei"]

        result = self.em.run_workflow(self.em.get_workflows()[0])
        print(result)
