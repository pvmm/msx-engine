import json
import urllib.parse

from nicegui import ui, events
from datatypes import Tile
from v9918 import PALETTE, DEFAULT_FG_COLOR, DEFAULT_BG_COLOR
from tileeditor import TileEditor

from constants import TILE_STORAGE_HEIGHT, CONTAINER_COLOR
from common import header, get_text_color, enable, add_handlers
from ui import UiMetatile


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


class StageEditor(ui.row):
    """UI for editing stage metatiles, allowing to create and manage metatiles."""
    project_tiles: list[UiMetatile]
    project_tiles_row: ui.row
    metatiles_row: ui.row
    # metatile_collection: list[UiMetatile]
    add_metatile_button: ui.button
    selected_metatile: UiMetatile | None
    selected_metatile_index: int | None
    metatile_editor: MetatileEditor
    palette: list[str] = PALETTE

    def __init__(self, parent: ui.element, background_tiles: list[UiMetatile]):
        super().__init__()
        self.parent = parent
        self.project_tiles = background_tiles
        self.build_ui()


    def update_tiles(self) -> None:
        print('Updating stage editor tiles...', len(self.project_tiles))
        self.project_tiles_row.clear()
        with self.project_tiles_row:
            for metatile in self.project_tiles:
                UiMetatile(metatile.grid, PALETTE)
        print('done!')


    def on_select_metatile(self, event: events.GenericEventArguments) -> None:
        if self.selected_metatile:
            self.selected_metatile.style('border: 1px solid #444;')
        if isinstance(event.sender, UiMetatile):
            self.selected_metatile = event.sender
            self.selected_metatile.style('border: 3px solid #444;')


    def add_metatile(self, bgcolor_index: int) -> UiMetatile:
        with self.metatiles_row:
            metatile = UiMetatile(Tile(None, None, None), PALETTE) \
                    .move(target_index=0).on('mousedown', lambda e: self.on_select_metatile(e))
            return metatile


    def on_add_metatile_clicked(self, event: events.ClickEventArguments) -> None:
        # Add ui card with 3 tiles
        if self.selected_metatile_index:
            self.add_metatile(self.selected_metatile_index)


    def erase_selected_tile(self) -> None:
        if self.selected_metatile_index:
            self.project_tiles.pop(self.selected_metatile_index)
        if self.selected_metatile:
            self.selected_metatile.delete()
        self.selected_tile_index = None
        self.enable_tile_buttons(False)


    def on_erase_tile(self, event: events.ClickEventArguments) -> None:
        self.erase_selected_tile()


    def build_ui(self) -> None:
        with self.parent as parent:
            parent.classes('w-full')
            header('Stage metatile editor')

            header('Project tiles')

            with ui.row().classes('gap-8 w-full'):
                with ui.row().classes('items-center flex-nowrap'):
                    # background colour container
                    with ui.row().classes('items-start gap-2 px-2 pt-2 w-full') as self.project_tiles_row:
                        self.project_tiles_row.style(
                            f'''background-color: {CONTAINER_COLOR};
                                height: {TILE_STORAGE_HEIGHT}px;
                                overflow-y: auto;'''
                        )
                        ui.space()

                    text = 'Create metafile from selected background tile'
                    self.add_metatile_button = \
                            ui.button(icon='fa-solid fa-angle-down',
                            on_click=lambda e: self.on_add_metatile_clicked(e)).tooltip(text).props('disabled')

            header('Available metatiles')

            # metatile container
            with ui.row().classes('items-start gap-2 px-2 pt-2 w-full') as self.metatiles_row:
                self.metatiles_row.style(
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


    # def select_background_tile(self, card: ui.card, index: int) -> ui.card:
    #     # unselect previous tile
    #     if self.selected_metatile:
    #         self.selected_metatile.style('border: 1px solid #444;')
    #     # select new tile
    #     self.selected_metatile = card.style('border: 3px solid #444;')
    #     self.selected_metatile_index = index
    #     self.enable_tile_buttons()
    #     return card


    # def on_select_background_tile(self, event: events.GenericEventArguments, index: int) -> None:
    #     if isinstance(event.sender, ui.card):
    #         self.select_background_tile(event.sender, index)


    def enable_tile_buttons(self, status: bool = True) -> None:
        enable(self.add_metatile_button, status)


    def on_add_background_tile(self, event: events.ClickEventArguments, index: int) -> None:
        color: str = self.palette[index]
        # color: str = event.sender._props.get('color')
        # self.add_background_tile(index, color)


@ui.page('/')
def main() -> None:
    add_handlers()
    with ui.row().classes('w-full'):
        alist: list[UiMetatile] = []
        StageEditor(ui.column().classes('w-full min-h-screen p-0 m-0'), alist)


if __name__ in {"__main__", "__mp_main__"}:
    from common import run
    run('NiceGui app')
