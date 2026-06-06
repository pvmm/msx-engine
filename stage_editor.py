from nicegui import ui, events
from typing import List, Tuple
from v9918 import PALETTE, divide_colors

from common import get_text_color, menu_item

TILE_PIXEL_SIZE = 12
TILE_STORAGE_HEIGHT = 50
CONTAINER_COLOR = '#e0e0e0'

class StageEditor:
    background_tile_cards = None
    add_metatile_button = None

    def __init__(self, parent):
        self.parent = parent
        self.background_tiles = set()
        self.selected_tile = None
        self.build_ui()

    def on_add_metatile_clicked(self, event: events.ClickEventArguments) -> None:
        print(event)

    def build_ui(self) -> None:
        with self.parent as parent:
            parent.classes('w-full')
            ui.label('Stage metatile collection').classes('text-lg font-semibold')
            with ui.row().classes('items-center flex-nowrap'):
                ui.label('Add background tile by color:')
                self.draw_color_dropdown(PALETTE)

            self.background_tile_colors_label = ui.label('Available background tiles:')

            # background colour container
            with ui.row().classes('items-center gap-2 px-2 w-full') \
                    .style(f'background-color: {CONTAINER_COLOR}; height: {TILE_STORAGE_HEIGHT}px; overflow-y: auto;') \
                    as self.background_tile_cards:
                ui.space()
            self.add_metatile_button = ui.button('Add metatile...',
                 on_click=lambda e: self.on_add_metatile_clicked(e)).props('disabled')

    def set_background_tile_style(self, element: ui.element, color = '#000000') -> None:
        return element.style(
            f'''
            width: {TILE_PIXEL_SIZE}px;
            height: {TILE_PIXEL_SIZE}px;
            background-color: {color};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )

    def select_background_tile(self, element: ui.element) -> ui.element:
        if self.selected_tile:
            self.selected_tile.style('border: 1px solid #444;')
        self.selected_tile = element.style('border: 3px solid #444;')
        return element

    def on_select_background_tile(self, e: events.GenericEventArguments) -> None:
        self.select_background_tile(e.sender)

    def add_background_tile(self, index, color) -> ui.element:
        pos = len(self.background_tiles)
        self.background_tiles.add(index)
        if pos == len(self.background_tiles):
            return
        self.add_metatile_button._props.pop('disabled')
        with self.background_tile_cards:
            return self.select_background_tile(
                    self.set_background_tile_style(
                        ui.card().on('mousedown', lambda e: self.on_select_background_tile(e)) \
                                .tooltip(f'color #{index} ({color})').move(target_index = pos),
                                color
                    )
                )

    def on_add_background_tile(self, event, index) -> None:
        color = event.sender._props.get('color')
        self.add_background_tile(index, color)

    def draw_color_dropdown(self, palette) -> None:
        with ui.dropdown_button('select color', auto_close=True):
            for index, color in enumerate(palette[1:], start=1):
                ui.item(f'color {index}', on_click=lambda e, i=index: self.on_add_background_tile(e, i)) \
                    .style(f'''
                        background-color: {color};
                        color: {get_text_color(color)};
                    ''') \
                    .props(f'{color=}')

if __name__ in {"__main__", "__mp_main__"}:
    ui.add_head_html('<script src="https://kit.fontawesome.com/e374aa0b36.js" crossorigin="anonymous"></script>')
    ui.add_css('.q-tooltip { font-size: 18px; white-space: pre-line; }')
    with ui.row().classes('w-full'):
        StageEditor(ui.column())
    ui.run(
        title='NiceGUI Tile Editor'
    )
