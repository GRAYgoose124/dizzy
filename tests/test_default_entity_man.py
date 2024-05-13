from dizzy.daemon import DaemonEntityManager


class TestServices:
    def setup_method(self):
        self.em = DaemonEntityManager()

    def test_daemon_entity_manager(self):
        # should have project and status services in it
        # self.em.sm.services
        assert all(
            [
                s.name in ["uno", "project", "status"]
                for s in self.em.csm.services.values()
            ]
        )

        # find all entities, should be einz, zwei, drei
        assert all(
            [e.name in ["einz", "zwei", "drei"] for e in self.em.entities.values()]
        )

    def test_project_service(self):
        assert self.em.find_service("project").name == "project"

    def test_status_service(self):
        assert self.em.find_service("status").name == "status"
