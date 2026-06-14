import json
import urllib.parse

from nicegui import ui, events
from nicegui.elements.interactive_image import InteractiveImage
from v9918 import PALETTE, DEFAULT_FG_COLOR, DEFAULT_BG_COLOR, Tile8x8, grid_to_svg
from tileeditor import TileEditor

from constants import TILE_STORAGE_HEIGHT, CONTAINER_COLOR
from common import header, get_text_color


TILE_PIXEL_SIZE = 12
METATILE_STORAGE_HEIGHT = 100


class MetatileEditor:
    """UI for editing a metatile, allowing to modify its properties and tiles."""
    parent: ui.element
    tile_editor: TileEditor

    def __init__(self, parent: ui.element, metatile: UiMetatile | None = None):
        self.parent = parent
        self.metatile = metatile
        self.build_ui()


    def build_ui(self) -> None:
        with self.parent:
            ui.checkbox('Scrollable metatile')
            self.tile_editor = TileEditor(parent=ui.column())
        if self.metatile:
            self.parent.props('enabled')
        else:
            self.parent.props('disabled')


    def update(self, metatile: UiMetatile) -> None:
        self.metatile = metatile
        if self.metatile:
            self.parent.props('enabled')
        else:
            self.parent.props('disabled')


class UiMetatile(InteractiveImage):
    """Represents a metatile in the UI, allowing to display and select/unselect it."""
    grid: Tile8x8

    def __init__(self, data: str | Tile8x8 | None = None, scale: int = 5):
        with self:
            self.scale = scale
            if not data:
                grid = Tile8x8(DEFAULT_FG_COLOR, DEFAULT_BG_COLOR)
            elif isinstance(data, Tile8x8):
                grid = data
            else:
                # Convert from json string
                grid = json.loads(data)
            self.reload(grid)


    def reload(self, grid: Tile8x8) -> None:
        self.grid = grid
        data = grid_to_svg(self.grid, self.scale)
        self.ui = self.set_source('data:image/svg+xml;utf8,' + urllib.parse.quote(data))


class StageEditor:
    """UI for editing stage metatiles, allowing to create and manage metatiles."""
    background_tiles: set[int]
    background_tile_cards: ui.row
    metatile_container: ui.row
    metatile_collection: list[UiMetatile]
    add_metatile_button: ui.button
    erase_background_tile_button: ui.button
    selected_tile_card: ui.card
    selected_tile_index: int | None
    selected_metatile_element: ui.element | None
    metatile_editor: MetatileEditor
    palette: list[str] = PALETTE

    def __init__(self, parent: ui.element):
        self.parent = parent
        self.background_tiles = set()
        self.build_ui()


    def on_select_metatile(self, event: events.GenericEventArguments) -> None:
        if self.selected_metatile_element:
            self.selected_metatile_element.style('border: 1px solid #444;')
        self.selected_metatile_element = event.sender
        self.selected_metatile_element.style('border: 3px solid #444;')
        #self.metatile_editor.update(self.selected_metatile_element)


    def add_metatile(self, bgcolor_index: int) -> UiMetatile:
        with self.metatile_container:
            metatile = UiMetatile(grid_to_svg(Tile8x8(15, bgcolor_index), 5)) \
                    .move(target_index=0).on('mousedown', lambda e: self.on_select_metatile(e))
            self.metatile_collection.append(metatile)
            return metatile


    def on_add_metatile_clicked(self, event: events.ClickEventArguments) -> None:
        # Add ui card with 3 tiles
        if self.selected_tile_index:
            self.add_metatile(self.selected_tile_index)


    def erase_selected_tile(self) -> None:
        if self.selected_tile_index:
            self.background_tiles.remove(self.selected_tile_index)
        if self.selected_tile_card:
            self.selected_tile_card.delete()
        self.selected_tile_index = None
        self.enable_tile_buttons(False)


    def on_erase_tile(self, event: events.ClickEventArguments) -> None:
        self.erase_selected_tile()


    def build_ui(self) -> None:
        with self.parent as parent:
            parent.classes('w-full')
            header('Stage metatile collection')

            header('Background tiles')

            with ui.row().classes('gap-8 w-full'):
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Add background tile by color').classes('whitespace-nowrap')
                    self.draw_color_dropdown(self.palette)

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
            with ui.row().classes('items-start gap-2 px-2 pt-2 w-full') as self.metatile_container:
                self.metatile_container.style(
                        f'''background-color: {CONTAINER_COLOR};
                        height: {METATILE_STORAGE_HEIGHT}px;
                        overflow-y: auto;''')
                ui.space()

            self.metatile_editor = MetatileEditor(ui.card().classes('w-full'))


    def set_background_tile_style(self, element: ui.element, color: str = '#000000') -> None:
        element.style(
            f'''
            width: {TILE_PIXEL_SIZE}px;
            height: {TILE_PIXEL_SIZE}px;
            background-color: {color};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )


    def select_background_tile(self, card: ui.card, index: int) -> ui.card:
        # unselect previous tile
        if self.selected_tile_card:
            self.selected_tile_card.style('border: 1px solid #444;')
        # select new tile
        self.selected_tile_card = card.style('border: 3px solid #444;')
        self.selected_tile_index = index
        self.enable_tile_buttons()
        return card


    def on_select_background_tile(self, event: events.GenericEventArguments, index: int) -> None:
        if isinstance(event.sender, ui.card):
            self.select_background_tile(event.sender, index)


    def add_background_tile(self, index: int, color: str) -> ui.element | None:
        pos = len(self.background_tiles)
        self.background_tiles.add(index)
        if pos == len(self.background_tiles): return None
        with self.background_tile_cards:
            card = ui.card().on('mousedown', lambda e, i=index: self.on_select_background_tile(e, i))
            card.tooltip(f'color #{index} ({color})').move(target_index = pos)
            self.set_background_tile_style(card, color)
            self.select_background_tile(card, index)
        return card


    def enable_tile_buttons(self, status: bool = True) -> None:
        if status:
            self.erase_background_tile_button.props('enabled')
            self.add_metatile_button.props('enabled')
        else:
            self.erase_background_tile_button.props('disabled')
            self.add_metatile_button.props('disabled')


    def on_add_background_tile(self, event: events.ClickEventArguments, index: int) -> None:
        color: str = self.palette[index]
        # color: str = event.sender._props.get('color')
        self.add_background_tile(index, color)


    def draw_color_dropdown(self, palette: list[str]) -> None:
        with ui.dropdown_button('select color', auto_close=True):
            for index, color in enumerate(palette[1:], start=1):
                ui.item(f'color {index}', on_click=lambda e, i=index: self.on_add_background_tile(e, i)) \
                    .style(f'''
                        background-color: {color};
                        color: {get_text_color(color)};
                    ''') \
                    .props(f'{color=}')


if __name__ in {"__main__", "__mp_main__"}:
    from common import run
    with ui.row().classes('w-full'):
        StageEditor(ui.column().classes('w-full min-h-screen p-0 m-0'))
    run()
