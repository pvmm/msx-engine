from nicegui import ui, app, events
from PIL import Image
import base64
from io import BytesIO

import bmpto105
from bmpto105 import BmpTo105

from common import run, add_handlers, file_to_base64, disable, enable
from fileloader import FileLoader


PALETTE = [
    (0, 0, 0), (0, 0, 0), (0x24, 0xda, 0x24), (0x68, 0xff, 0x68), (0x24, 0x24, 0xff), (0x48, 0x68, 0xff),
    (0xb6, 0x24, 0x24), (0x48, 0xda, 0xff), (0xff, 0x24, 0x24), (0xff, 0x68, 0x68), (0xda, 0xda, 0x24),
    (0xda, 0xda, 0x91), (0x24, 0x91, 0x24), (0xda, 0x48, 0xb6), (0xb6, 0xb6, 0xb6), (0xff, 0xff, 0xff)
]


class TileViewer:
    zoom: int;
    grid_width: int
    grid_height: int
    selected_x: int
    selected_y: int
    image: Image;
    image64: str;

    ui.add_css('''
        .pixelated {
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }
    ''', shared=True)

    # widgets
    grid_width_number: ui.element
    grid_height_number: ui.element

    def __init__(self, image: Image | None = None):
        self.engine = BmpTo105(PALETTE)
        self.zoom = 4
        self.grid_width = 8
        self.grid_height = 8
        self.selected_x = -1
        self.selected_y = -1
        self.build_ui()


    def build_ui(self):
        ui.add_head_html('<script src="/static/tileviewer.js"></script>', shared=True)
        with ui.column().classes('w-full h-screen'):

            with ui.row().classes('items-end flex-nowrap') as parent:
                FileLoader(parent, on_loaded=self.load_image, on_removed=self.remove_image)
                self.grid_width_number = disable(ui.number(label='Metatile Width', min=8, value=8, step=8, format='%i',
                          on_change=lambda e: self.on_change_grid_size('w', e),
                          validation={'metatile size mismatch': lambda value: self.image.size[0] % value == 0}))
                self.grid_height_number = disable(ui.number(label='Metatile Height', min=8, value=8, step=8, format='%i',
                          on_change=lambda e: self.on_change_grid_size('h', e),
                          validation={'metatile size mismatch': lambda value: self.image.size[1] % value == 0}))

            ui.slider(
                min=1,
                max=16,
                value=self.zoom,
                step=1,
                on_change=lambda e: self.set_zoom(int(e.value)),
            )

            with ui.scroll_area().classes('w-full flex-1 border'):
                ui.html(
                    '<canvas id="tile_canvas" class="pixelated"></canvas>'
                )

        ui.on("tile_clicked", self.on_tile_clicked)


    def load_image(self, data: bytes) -> None:
        image = Image.open(BytesIO(data))
        self.msx_image = self.engine.convert(image)
        self.image = self.msx_image.to_image()

        buffer = BytesIO()
        self.image.save(buffer, format='PNG')
        self.image64 = file_to_base64(buffer)
        self.grid_width_number.set_value(8);
        enable(self.grid_width_number)
        self.grid_height_number.set_value(8);
        enable(self.grid_height_number)

        ui.run_javascript(f"""
            window.tileViewer.initialize({{
                canvasId: "tile_canvas",
                image: "{self.image64}",
                zoom: {self.zoom}
            }});
        """)


    def remove_image(self, event: events.GenericEventArguments) -> None:
        disable(self.grid_width_number)
        disable(self.grid_height_number)
        ui.run_javascript('window.tileViewer.reset();');


    def on_change_grid_size(self, type: str, event: events.ValueChangeEventArguments[int | None]) -> None:
        if self.image:
            if type == 'w': self.grid_width = event.value
            if type == 'h': self.grid_height = event.value
            print('redraw!')
            self.redraw()


    def redraw(self):
        ui.run_javascript(f"""
            window.tileViewer.setState({{
                zoom: {self.zoom},
                selectedX: {self.selected_x},
                selectedY: {self.selected_y},
                gridWidth: {self.grid_width},
                gridHeight: {self.grid_height}
            }});
            window.tileViewer.draw();
        """)


    def set_zoom(self, zoom):
        self.zoom = zoom
        self.redraw()


    def on_tile_clicked(self, e):
        self.selected_x = e.args["col"] * self.grid_width
        self.selected_y = e.args["row"] * self.grid_height
        print(self.selected_x, self.selected_y)
        self.redraw()


@ui.page('/')
def main() -> None:
    add_handlers()
    # load local file
    #TileViewer(Image.open(IMAGE_FILE).convert('RGBA'))
    TileViewer()


if __name__ in {"__main__", "__mp_main__"}:
    from common import run
    run()
