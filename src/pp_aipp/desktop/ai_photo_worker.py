from __future__ import annotations

from pp_aipp.ai_photography import generate_recipe_photos

from .qt import QtCore


class AIPhotoWorker(QtCore.QObject):
    progress = QtCore.Signal(int, str)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, project_path, api_key: str, batch_size: int, quality: str, provider: str):
        super().__init__()
        self.project_path = project_path
        self.api_key = api_key
        self.batch_size = batch_size
        self.quality = quality
        self.provider = provider

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = generate_recipe_photos(
                self.project_path,
                self.api_key,
                batch_size=self.batch_size,
                quality=self.quality,
                provider=self.provider,
                progress_callback=self.progress.emit,
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - thread boundary reports the failure.
            self.failed.emit(str(exc))
        finally:
            self.api_key = ""
