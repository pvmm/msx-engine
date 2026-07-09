from nicegui import ui, events
from common import file_to_base64


class FileLoader(ui.column):
    def __init__(self, parent: ui.element, on_load: Callable[[], None]):
        with parent:
            super().__init__()
            self.parent = parent
            self.onload = on_load
            self.build_ui()


    def build_ui(self) -> None:
        with self.classes('gap-1 w-full'):
            ui.upload(
                on_upload=self.handle_upload,
                on_rejected=lambda e: print('file was rejected'),
                max_files=1
            ).props('auto-upload hide-upload-btn w-full accept=.png')


    async def handle_upload(self, e: events.UploadEventArguments) -> None:
        """Processes the dropped/uploaded image file."""
        ui.notify(f'"{e.file.name}" uploaded')
        self.onload(await e.file.read())
