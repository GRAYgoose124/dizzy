from pathlib import Path

import pytest
from dizzy.daemon import all_entities, DaemonEntityManager, BaseRequest, BaseResponse
from dizzy.utils import DependencyError


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
        assert all(wf in ["love", "einzy", "info", "hubris"] for wf in workflow_names)
        workflow_entities = [w[0] for w in workflows]
        assert all(e in ["zwei", "einz", "einz", "drei"] for e in workflow_entities)

        result = self.em.run_workflow(self.em.get_workflows()[0])
        print(result)

    def test_taskservice(self):
        service = self.em.find_service("uno")
        assert service is not None

        tasks = service.get_tasks()
        assert len(tasks) == 4

        task = tasks[0]
        assert task.name in ["A", "B", "C", "D"]
        assert all(e in ["entity_info", "service_info"] for e in task.requested_actions)

    def test_request_response(self):
        request = BaseRequest(
            entity="einz",
            workflow="einzy",
            ctx={"name": "dizzy", "age": 42},
        )

        response = BaseResponse.from_request(request)
        response.requester = "requester"

        assert response.requester == "requester"
        assert response.request.ctx == {"name": "dizzy", "age": 42}

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
