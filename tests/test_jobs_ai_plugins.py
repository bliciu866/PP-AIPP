from pp_aipp.core.ai import AIGateway, AIRequest, AIResponse
from pp_aipp.core.jobs import JobEngine
from pp_aipp.core.models import Job, JobStatus, Provenance
from pp_aipp.core.plugins import PluginManager
from pp_aipp.plugins.base import Plugin, PluginMetadata


class DemoProvider:
    name = "demo"
    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(request.content.upper(), self.name, "demo-model")


class DemoPlugin(Plugin):
    metadata = PluginMetadata("demo", "1.0", "Demo plugin")
    def activate(self, kernel: object) -> None:
        kernel.demo_active = True


def test_job_engine_success() -> None:
    job = JobEngine().run(Job("x", {"n": 2}), lambda p: {"n": p["n"] * 2})
    assert job.status is JobStatus.SUCCEEDED
    assert job.result == {"n": 4}


def test_ai_gateway_marks_draft() -> None:
    gateway = AIGateway()
    gateway.register(DemoProvider())
    response = gateway.generate("demo", AIRequest("edit", "hello", {}))
    assert response.content == "HELLO"
    assert response.provenance is Provenance.EDITORIAL_DRAFT


def test_plugin_manager() -> None:
    manager = PluginManager()
    manager.register(DemoPlugin())
    class Kernel: pass
    kernel = Kernel()
    manager.activate_all(kernel)
    assert kernel.demo_active is True
