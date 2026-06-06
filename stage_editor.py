from nicegui import ui, events
from typing import List, Tuple
from v9918 import PALETTE, divide_colors

from common import header, get_text_color, menu_item

TILE_PIXEL_SIZE = 12
TILE_STORAGE_HEIGHT = 50
CONTAINER_COLOR = '#e0e0e0'

class StageEditor:
    background_tile_cards = None
    metatile_cards = None
    add_metatile_button = None
    erase_background_tile_button = None
    selected_tile_card = None
    selected_tile_index = None

    def __init__(self, parent):
        self.parent = parent
        self.background_tiles = set()
        self.build_ui()

    def on_add_metatile_clicked(self, event: events.ClickEventArguments) -> None:
        # Add ui card with 3 tiles
        print(event)

    def erase_selected_tile(self) -> None:
        self.background_tiles.remove(self.selected_tile_index)
        self.selected_tile_card.delete()
        self.selected_tile_index = None
        self.enable_tile_buttons(False)

    def on_erase_tile(self, event) -> None:
        self.erase_selected_tile()

    def build_ui(self) -> None:
        with self.parent as parent:
            parent.classes('w-full')
            header('Stage metatile collection')

            header('Background tiles')

            with ui.row().classes('gap-8 w-full'):
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Add background tile by color').classes('whitespace-nowrap')
                    self.draw_color_dropdown(PALETTE)

                    # background colour container
                    with ui.row().classes('items-center gap-2 px-2 min-w-[400px]') as self.background_tile_cards:
                        self.background_tile_cards.style(
                            f'''background-color: {CONTAINER_COLOR};
                                height: {TILE_STORAGE_HEIGHT}px;
                                overflow-y: auto;'''
                        )
                        ui.space()

                    text = 'Erase selected background tile'
                    self.erase_background_tile_button = \
                            ui.button(icon='fa-solid fa-minus',
                            on_click=self.on_erase_tile).tooltip(text).props('disabled')

                    text = 'Create metafile from selected background tile'
                    self.add_metatile_button = \
                            ui.button(icon='fa-solid fa-angle-down',
                            on_click=lambda e: self.on_add_metatile_clicked(e)).tooltip(text).props('disabled')

            header('Available metatiles')

            # metatile container
            with ui.row().classes('items-center gap-2 px-2 w-full') as self.metatile_cards:
                self.metatile_cards.style(
                        f'''background-color: {CONTAINER_COLOR};
                        height: {TILE_STORAGE_HEIGHT}px;
                        overflow-y: auto;''')
                ui.space()

            header('Selected metatile')

            ui.checkbox('Scrollable metatile')

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

    def select_background_tile(self, element: ui.element, index: int) -> ui.element:
        if self.selected_tile_card:
            self.selected_tile_card.style('border: 1px solid #444;')
        self.selected_tile_card = element.style('border: 3px solid #444;')
        self.selected_tile_index = index
        self.enable_tile_buttons(True)
        return element

    def on_select_background_tile(self, e: events.GenericEventArguments, index: int) -> None:
        self.select_background_tile(e.sender, index)

    def add_background_tile(self, index: int, color: str) -> ui.element:
        pos = len(self.background_tiles)
        self.background_tiles.add(index)
        if pos == len(self.background_tiles): return
        with self.background_tile_cards:
            return self.select_background_tile(
                    self.set_background_tile_style(
                        ui.card().on('mousedown', lambda e, i=index: self.on_select_background_tile(e, i)) \
                                .tooltip(f'color #{index} ({color})').move(target_index = pos),
                                color
                    ),
                index)

    def enable_tile_buttons(self, b: bool) -> None:
        if b:
            self.erase_background_tile_button._props.pop('disabled')
            self.add_metatile_button._props.pop('disabled')
        else:
            self.erase_background_tile_button.props('disabled')
            self.add_metatile_button.props('disabled')

    def on_add_background_tile(self, event, index: int) -> None:
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
