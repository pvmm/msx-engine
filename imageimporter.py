
from io import BytesIO
import base64

from PIL import Image
from nicegui import ui, events
from v9918 import TILE_SIZE


def file_to_base64(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/png;base64,{encoded}'


class FileLoader(ui.column):
    container: ui.scroll_area

    def __init__(self, parent: ui.element):
        with parent:
            super().__init__()
            self.parent = parent
            self.build_ui()


    def build_ui(self) -> None:
        with self.classes('gap-1 w-full'):
            ui.upload(
                on_upload=self.handle_upload,
                on_rejected=lambda e: print('file was rejected'),
                max_files=1
            ).props('auto-upload hide-upload-btn w-full accept=.png')
            self.container = ui.scroll_area().classes('gap-1 w-full p-0 m-0') \
                    .style('background-color: #ccc; height: 400px;')


    async def handle_upload(self, e: events.UploadEventArguments) -> None:
        """Processes the dropped/uploaded image file."""
        ui.notify(f'Uploaded: {e.file.name}')
        image = Image.open(BytesIO(await e.file.read()))
        self.build_tiles(image)


    def build_tiles(self, source: Image.Image) -> None:
        tiles_w = source.width // TILE_SIZE
        tiles_h = source.height // TILE_SIZE

        with self.container:
            for y in range(tiles_h):
                with ui.row().classes('w-full gap-1 p-0 m-0 items-center flex-nowrap'):
                    for x in range(tiles_w):
                        tile = source.crop((
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            (x + 1) * TILE_SIZE,
                            (y + 1) * TILE_SIZE,
                        ))
    
                        ui.image(file_to_base64(tile)).style(
                            'width:16px;height:16px;image-rendering:pixelated;'
                        )


FileLoader(ui.column().classes('w-full'))

ui.run()
