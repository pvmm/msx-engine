from collections.abc import Callable
from nicegui import ui, events


# supported image types
SUPPORTED_TYPES = '.png,.bmp,.gif'


class FileLoader(ui.column):

    def __init__(self, parent: ui.element, on_loaded: Callable[[], None], on_removed: Callable[[events.GenericEventArguments], None] | None = None):
        with parent:
            super().__init__()
            self.parent = parent
            self.on_loaded = on_loaded
            self.on_removed = on_removed
            self.build_ui()


    def build_ui(self) -> None:
        with self:
            with (
                ui.upload(
                    on_upload=self.handle_upload,
                    on_rejected=lambda e: print('file was rejected'),
                    max_files=1)
                .props(f'auto-upload hide-upload-btn w-full accept={SUPPORTED_TYPES}')
                .on('removed', self.on_removed)
            ).add_slot('list'):
                with ui.row().classes('flex-nowrap items-center justify-center'):
                    ui.icon('cloud_upload', size='lg')
                    ui.label('256x192 image')


    async def handle_upload(self, e: events.UploadEventArguments) -> None:
        """Processes the dropped/uploaded image file."""
        ui.notify(f'"{e.file.name}" uploaded')
        self.on_loaded(await e.file.read())
