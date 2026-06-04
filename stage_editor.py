from nicegui import ui
from typing import List, Tuple
from v9918 import PALETTE

from common import get_text_color, menu_item


class StageEditor:
    background_tile_colors_label = None

    def __init__(self, parent):
        self.parent = parent
        self.background_tiles = []
        self.build_ui()

    def build_ui(self):
        ui.label('Stage metatile collection').classes('text-lg font-semibold')
        with ui.row().classes('items-center flex-nowrap'):
            ui.label('Add background tile color:')
            self.draw_color_dropdown(PALETTE)

        self.background_tile_colors_label = ui.label(menu_item('background tile colors'))
        ui.button('Add metatile...', on_click=lambda e: ui.notify('button clicked!'))

    def on_add_background_tile(self, event):
        color = event.sender._props.get('color')
        self.background_tiles.append(color)
        with self.background_tile_colors_label:
            ui.fab_action('').style(f'background-color: {color}; color: {color}').props(f'{color=}')

    def draw_color_dropdown(self, palette):
        with ui.dropdown_button('select color', auto_close=True):
            for index, color in enumerate(palette[1:], start=1):
                ui.item(f'color {index}', on_click=lambda e: self.on_add_background_tile(e)) \
                    .style(f'''
                        background-color: {color};
                        color: {get_text_color(color)};
                    ''') \
                    .props(f'{color=}')

if __name__ == '__main__':
    ui.add_head_html('<script src="https://kit.fontawesome.com/e374aa0b36.js" crossorigin="anonymous"></script>')
    ui.add_css('.q-tooltip { font-size: 18px; white-space: pre-line; }')
    with ui.row():
        StageEditor(ui.column())

    ui.run(title='NiceGUI Stage Editor')
