from pathlib import Path

import pytest
from dizzy.daemon import all_entities, DaemonEntityManager, Request, Response


class TestProtocol:
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

    def test_request_response(self):
        request = Request(
            entity="einz",
            workflow="einzy",
            ctx={"name": "dizzy", "age": 42},
        )

        response = Response.from_request("requester", request)

        assert response.requester == "requester"
        assert response.ctx == {"name": "dizzy", "age": 42}

        response.set_result({"name": "dizzy", "age": 42})
        response.set_status("completed")

        assert response.status == "completed"
        assert response.result == {"name": "dizzy", "age": 42}

        response.add_error("TestError", "This is a test error")
        response.add_error("TestError", "This is a test error")

        assert response.errors == {
            "TestError": ["This is a test error", "This is a test error"]
        }

        response.add_info("TestInfo", "This is a test info")
        response.add_info("TestInfo", "This is a test info")

        assert response.info == {
            "TestInfo": ["This is a test info", "This is a test info"]
        }

        response.status = None
        response.set_status("completed")
        response.set_result({"name": "dizzy", "age": 42})

        assert response.status == "completed"
        assert response.result == {"name": "dizzy", "age": 42}

        response.set_status("error")
        with pytest.raises(RuntimeError):
            response.set_result({"name": "dizzy", "age": 42})

        assert response.status == "error"
        assert response.result == {"name": "dizzy", "age": 42}
