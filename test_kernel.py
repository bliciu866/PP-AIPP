from pathlib import Path

from pp_aipp.core.kernel import Kernel


def write_config(tmp_path: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
platform: {name: PP-AIPP}
paths:
  workspace_root: PLACEHOLDER/workspaces
  log_dir: PLACEHOLDER/logs
logging: {level: INFO, filename: test.log}
""".replace("PLACEHOLDER", str(tmp_path).replace("\\", "/")),
        encoding="utf-8",
    )
    return path


def test_kernel_lifecycle(tmp_path: Path) -> None:
    kernel = Kernel(write_config(tmp_path))
    assert kernel.health().status == "INITIALIZED"
    kernel.start()
    assert kernel.health().status == "READY"
    kernel.stop()
    assert kernel.started is False
