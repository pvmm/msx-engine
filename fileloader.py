from nicegui import ui, events
from common import file_to_base64


class FileLoader(ui.column):
    #container: ui.scroll_area

    def __init__(self, parent: ui.element, onload: Callable[[], None]):
        with parent:
            super().__init__()
            self.parent = parent
            self.onload = onload
            self.build_ui()


    def build_ui(self) -> None:
        with self.classes('gap-1 w-full'):
            ui.upload(
                on_upload=self.handle_upload,
                on_rejected=lambda e: print('file was rejected'),
                max_files=1
            ).props('auto-upload hide-upload-btn w-full accept=.png')
            #self.container = ui.scroll_area().classes('gap-1 w-full p-0 m-0') \
            #        .style('background-color: #ccc; height: 400px;')


    async def handle_upload(self, e: events.UploadEventArguments) -> None:
        """Processes the dropped/uploaded image file."""
        ui.notify(f'"{e.file.name}" uploaded')
        self.onload(await e.file.read())
        #image = Image.open(BytesIO(await e.file.read()))
        #self.build_tiles(image)
