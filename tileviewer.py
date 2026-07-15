from nicegui import ui, app, events
from PIL import Image
import base64
from io import BytesIO

import bmpto105
from bmpto105 import BmpTo105, MSXBitmap_105

import common
from common import run, add_handlers, file_to_base64, disable, enable

from constants import GRID_PIXEL_MAX
from fileloader import FileLoader
from datatypes import Tile, from_105_to_metatile
from tileeditor import TileEditor


PALETTE = [
    (0, 0, 0), (0, 0, 0), (0x24, 0xda, 0x24), (0x68, 0xff, 0x68), (0x24, 0x24, 0xff), (0x48, 0x68, 0xff),
    (0xb6, 0x24, 0x24), (0x48, 0xda, 0xff), (0xff, 0x24, 0x24), (0xff, 0x68, 0x68), (0xda, 0xda, 0x24),
    (0xda, 0xda, 0x91), (0x24, 0x91, 0x24), (0xda, 0x48, 0xb6), (0xb6, 0xb6, 0xb6), (0xff, 0xff, 0xff)
]


class TileViewer:
    reused_tiles: list[int, int, int]
    total_tiles: list[int, int, int]
    threshold: float
    zoom: int
    grid_width: int
    grid_height: int
    selected_x: int
    selected_y: int
    msx: MSXBitmap_105 | None
    #image: Image.Image | None;
    image64: str

    ui.add_css('''
        .pixelated {
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }
    ''', shared=True)

    # widgets
    grid_width_number: ui.element
    grid_height_number: ui.element
    tile_info_label: ui.label

    def __init__(self, image: Image.Image | None = None):
        self.msx = None
        if image: self.load_image(image)
        self.engine = BmpTo105(PALETTE)
        self.reused_tiles = [0, 0, 0]
        self.total_tiles = [0, 0, 0]
        self.threshold = 0.0
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
                with ui.column().classes('items-end flex-nowrap w-full'):
                    self.tile_info_label = ui.label('').classes('text-nowrap')
                    self.update_tile_info()
                    with ui.row().classes('items-end flex-nowrap'):
                        self.grid_width_number = disable(ui.number(label='Metatile Width', min=8, value=8, step=8, format='%i',
                              on_change=lambda e: self.on_change_grid_size('w', e),
                              validation={'metatile size mismatch': lambda value: self.image.size[0] % value == 0})
                                  .props('hide-bottom-space')
                        )
                        self.grid_height_number = disable(ui.number(label='Metatile Height', min=8, value=8, step=8, format='%i',
                              on_change=lambda e: self.on_change_grid_size('h', e),
                              validation={'metatile size mismatch': lambda value: self.image.size[1] % value == 0})
                                  .props('hide-bottom-space')
                        )

            ui.slider(
                min=1,
                max=16,
                value=self.zoom,
                step=1,
                on_change=lambda e: self.set_zoom(int(e.value)),
            )

            with ui.scroll_area().classes('w-full flex-1 border bg-gray-200').on('contextmenu.prevent', lambda: None):
                canvas = (
                    ui.element('canvas').props('id=tile_canvas').on('contextmenu.prevent', lambda: None)
                )

        ui.on("tile_clicked", self.on_tile_clicked)


    def update_tile_info(self) -> None:
        reused_tiles = '???/???/???' if not self.msx else '/'.join([str(n) for n in self.reused_tiles])
        total_tiles = '???/???/???' if not self.msx else '/'.join([str(n) for n in self.total_tiles])
        self.tile_info_label.set_text(f"tile info: {reused_tiles} reused tiles, {total_tiles} total tiles.")


    def load_image(self, data: bytes) -> None:
        image = Image.open(BytesIO(data))
        self.msx = self.engine.convert(image)

        # update tile info
        self.reused_tiles[0], self.total_tiles[0] = self.msx.stats2(0, 64, self.threshold)
        self.reused_tiles[1], self.total_tiles[1] = self.msx.stats2(64, 128, self.threshold)
        self.reused_tiles[2], self.total_tiles[2] = self.msx.stats2(128, 196, self.threshold)
        self.update_tile_info()

        self.image = self.msx.to_image()
        self.msx.save_bitmap('image.105.png')

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
            if type == 'w': self.grid_width = int(event.value)
            if type == 'h': self.grid_height = int(event.value)
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


    async def on_tile_clicked(self, e):
        print(e.args)
        self.selected_x = e.args['col'] * self.grid_width
        self.selected_y = e.args['row'] * self.grid_height
        self.redraw()

        frame = int(e.args['button'] // 2)
        data = self.msx.to_metatile(e.args['col'], e.args['row'] * self.grid_height,
                                    int(self.grid_width / 8), self.grid_height, frame)
        metatiles = from_105_to_metatile(data, self.grid_width, self.grid_height)

        width = min(common.SCREEN_WIDTH * 0.90, 260 + self.image.size[0] * GRID_PIXEL_MAX)
        with ui.dialog() as dialog, ui.card().style(f'max-width: None; width: {width}px;') as parent:
            editor = TileEditor(parent, metatiles)
            with ui.row().classes('w-full justify-end'):
                ui.button('OK', on_click=lambda: dialog.submit(True))
                ui.button('Cancel', on_click=lambda: dialog.submit(False))
        result = await dialog
        if result and editor and self.selected_tile:
            # return tile changes
            #self.selected_tile.reload(editor.grid)
            pass

