from typing import cast
from nicegui import ui, app, events, run
from PIL import Image
import base64
from io import BytesIO

from bmpto105 import BmpTo105, MSXBitmap_105

import common
from common import add_handlers, file_to_base64, disable, enable

from constants import GRID_PIXEL_MAX
from fileloader import FileLoader
from datatypes import Tile, from_105_to_metatile
from tileeditor import TileEditor
from imageslider import ImageSliderWidget


PALETTE = [
    (0, 0, 0), (0, 0, 0), (0x24, 0xda, 0x24), (0x68, 0xff, 0x68), (0x24, 0x24, 0xff), (0x48, 0x68, 0xff),
    (0xb6, 0x24, 0x24), (0x48, 0xda, 0xff), (0xff, 0x24, 0x24), (0xff, 0x68, 0x68), (0xda, 0xda, 0x24),
    (0xda, 0xda, 0x91), (0x24, 0x91, 0x24), (0xda, 0x48, 0xb6), (0xb6, 0xb6, 0xb6), (0xff, 0xff, 0xff)
]


class TileViewer:
    processing_tiles: bool
    reuse_tiles: list[int]
    total_tiles: list[int]
    threshold: float
    zoom: int
    grid_width: int
    grid_height: int
    selected_x: int
    selected_y: int
    msx: MSXBitmap_105 | None
    image: Image.Image
    image0: Image.Image
    image1: Image.Image
    image64: str

    ui.add_css('''
        .pixelated {
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }
    ''', shared=True)

    # widgets
    grid_width_number: ui.number
    grid_height_number: ui.number
    threshold_number: ui.number
    reuse_badges: list[ui.badge]
    total_badges: list[ui.badge]

    def __init__(self, image: Image.Image | None = None) -> None:
        self.msx = None
        if image: self.set_image(image)
        self.processing_tiles = False
        self.engine = BmpTo105(PALETTE)
        self.reuse_tiles = [0, 0, 0]
        self.total_tiles = [0, 0, 0]
        self.threshold = 0.0
        self.zoom = 4
        self.grid_width = 8
        self.grid_height = 8
        self.selected_x = -1
        self.selected_y = -1
        self.build_ui()


    def build_ui(self) -> None:
        ui.add_head_html('<script src="/static/tileviewer.js"></script>', shared=True)
        with ui.column().classes('w-full h-screen'):
            ImageSliderWidget('./samples', 256, 192, on_loaded=self.load_image, on_removed=self.remove_image)

            with ui.scroll_area().classes('w-full flex-1 border bg-gray-200').on('contextmenu.prevent', lambda: None):
                canvas = (
                    ui.element('canvas').props('id=tile_canvas').on('contextmenu.prevent', lambda: None)
                )

            with ui.row().classes('items-end flex-nowrap w-full') as parent:
                (
                    ui.slider(min=1, max=16, value=self.zoom, step=1,
                              on_change=lambda e: self.set_zoom(int(e.value)))
                        .props('vertical reverse')
                        .classes('h-[120px]')
                )

                with ui.column().classes('items-start flex-nowrap w-full'):

                    self.reuse_badges = []
                    self.total_badges = []
                    with ui.row().classes('flex-nowrap items-center'):
                        ui.label('Tiles reused:')
                        self.reuse_badges.append(ui.badge('0', color='purple').tooltip('top 64x8 tiles'))
                        ui.label('/')
                        self.reuse_badges.append(ui.badge('0', color='purple').tooltip('middle 64x8 tiles'))
                        ui.label('/')
                        self.reuse_badges.append(ui.badge('0', color='purple').tooltip('bottom 64x8 tiles'))
                        ui.label('Tiles total:')
                        self.total_badges.append(ui.badge('0', color='purple').tooltip('top 64x8 tiles'))
                        ui.label('/')
                        self.total_badges.append(ui.badge('0', color='purple').tooltip('middle 64x8 tiles'))
                        ui.label('/')
                        self.total_badges.append(ui.badge('0', color='purple').tooltip('bottom 64x8 tiles'))

                    with ui.row().classes('items-start flex-nowrap w-full'):
                        self.grid_width_number = cast(ui.number, disable(
                                ui.number(label='Metatile Width', min=8, value=8, step=8, format='%i',
                                          on_change=lambda e: self.on_change_grid_size('w', e),
                                          validation={'metatile size mismatch': lambda value: self.image.size[0] % value == 0})
                        ))
                        self.grid_height_number = cast(ui.number, disable(
                                ui.number(label='Metatile Height', min=8, value=8, step=8, format='%i',
                                          on_change=lambda e: self.on_change_grid_size('h', e),
                                          validation={'metatile size mismatch': lambda value: self.image.size[1] % value == 0})
                        ))
                        self.threshold_number = cast(ui.number, disable(
                                ui.number(label='DCT Threshold', min=0.0, value=0.0, step=0.1, max=1.0, format='%0.1f',
                                          on_change=self.on_change_threshold).classes('w-[170px]').props('debounce=500')
                        ))


        ui.on("tile_clicked", self.on_tile_clicked)


    def update_tile_info(self) -> None:
        for n in range(3):
            self.reuse_badges[n].set_text(str(self.reuse_tiles[n]))
            bg = 'red' if self.total_tiles[n] > 255 else ('yellow' if self.total_tiles[n] > 200 else 'green')
            fg = 'black' if bg == 'yellow' else 'white'
            self.total_badges[n].set_text_color(fg)
            self.total_badges[n].set_background_color(bg)
            self.total_badges[n].set_text(str(self.total_tiles[n]))
        enable(self.threshold_number)


    def load_image(self, data: bytes) -> None:
        try:
            image = Image.open(BytesIO(data)).convert("RGB")
        except Exception as e:
            ui.notify(e)
            return

        self.set_image(image)


    def set_image(self, image: Image.Image) -> None:
        try:
            self.msx = self.engine.convert(image)
        except Exception as e:
            ui.notify(e)
            return

        # update tile info
        self.reuse_tiles, self.total_tiles = process_tiles(self.threshold, self.msx)
        self.update_tile_info()

        buffer = BytesIO()
        self.image = self.msx.to_image()
        self.image.save(buffer, format='PNG')
        self.image64 = file_to_base64(buffer)

        self.grid_width_number.set_value(8);
        enable(self.grid_width_number)

        self.grid_height_number.set_value(8);
        enable(self.grid_height_number)

        self.threshold_number.set_value(0.0);
        enable(self.threshold_number)

        ui.run_javascript(f"""
            window.tileViewer.initialize({{
                canvasId: "tile_canvas",
                image: "{self.image64}",
                zoom: {self.zoom}
            }});
        """)


    def remove_image(self) -> None:
        if self.msx:
            disable(self.grid_width_number)
            disable(self.grid_height_number)
            disable(self.threshold_number)
            ui.run_javascript('window.tileViewer.reset();');


    def on_remove_image(self, event: events.GenericEventArguments) -> None:
        self.remove_image()


    def on_change_grid_size(self, type: str, event: events.ValueChangeEventArguments[int | None]) -> None:
        if self.msx:
            if type == 'w': self.grid_width = cast(int, event.value)
            if type == 'h': self.grid_height = cast(int, event.value)
            self.redraw()


    async def on_change_threshold(self, event: events.ValueChangeEventArguments[float | None]) -> None:
        disable(self.threshold_number)
        if self.processing_tiles or not self.msx:
            return
        self.processing_tiles = True
        try:
            self.threshold = cast(float, event.value)
            self.reuse_tiles, self.total_tiles = await run.io_bound(process_tiles, cast(float, event.value), self.msx)
        finally:
            self.processing_tiles = False
            self.update_tile_info()
            enable(self.threshold_number)


    def redraw(self) -> None:
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


    def set_zoom(self, zoom: int) -> None:
        self.zoom = zoom
        self.redraw()


    async def on_tile_clicked(self, e: events.GenericEventArguments) -> None:
        if not self.msx:
            return
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


def process_tiles(threshold: float, msx: MSXBitmap_105) -> tuple[list[int], list[int]]:
    """Run outside class so we don't have to pickle it."""
    reuse_tiles, total_tiles = [0, 0, 0], [0, 0, 0]
    reuse_tiles[0], total_tiles[0] = msx.stats(0, 64, threshold)
    reuse_tiles[1], total_tiles[1] = msx.stats(64, 128, threshold)
    reuse_tiles[2], total_tiles[2] = msx.stats(128, 196, threshold)

    return reuse_tiles, total_tiles

