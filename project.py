from nicegui import ui, events
from tileeditor import TileEditor
from stageeditor import UiMetatile
from common import header, get_text_color, enable
from v9918 import PALETTE, DEFAULT_FG_COLOR, Tile8x8
from constants import TILE_STORAGE_HEIGHT, CONTAINER_COLOR, TILE_PIXEL_SIZE


# constants
PROJECT_TYPES = {
        'static screen': {
            'icon': 'check_box_outline_blank',
            'tooltip': '''screen doesn't move''',
            'scrolling': False,
        },
        'automatic L2R scrolling' : {
            'icon': 'trending_flat',
            'tooltip': '''screen always moves L2R,\nlike a SHMUP game''',
            'scrolling': True,
        },
        'scroll L2R when player moves': {
            'icon': 'start',
            'tooltip': '''screen scrolls when player moves towards the\nright edge of the screen, like a beat'em up''',
            'scrolling': True,
        },
        'free side scrolling': {
            'icon': 'swap_horiz',
            'tooltip': '''screen scrolls left or right when player moves towards the\nleft or right edge of the screen, like Atari 2600 Defender''',
            'scrolling': True,
        }
}
TARGET_OPTIONS = ['MSX1', 'MSX2 or above']
FRAME_RATE_OPTIONS = ['60Hz', '50Hz']
ROM_OPTIONS = ['8K', '16K']
FPS_OPTIONS = ['frame rate', 'half the frame rate', 'quarter the frame rate']


class Project:
    # settings
    background_tiles: list[UiMetatile]
    target = TARGET_OPTIONS[0]
    available_tiles: int = 256
    scrolling_tiles: int = available_tiles
    palette: bool = False
    r18_hardware_scroll: bool = False
    megarom: bool = False
    force_frame_rate: bool = False
    frame_rate: str = FRAME_RATE_OPTIONS[0]
    rom_type: str = ROM_OPTIONS[0]
    _105_color_mode: bool = False
    fps: int = FPS_OPTIONS.index('frame rate')
    scroll_pixels: int = 8
    project_type: str = 'static screen'
    project_changed: bool = True
    tiles_changed: bool = False
    initialized = False

    # ui elements
    scrolling_tiles_badge: ui.badge
    frame_rate_badge: ui.badge
    frame_rate_radio: ui.radio
    fps_badge: ui.badge
    target_badge: ui.badge
    second_pattern_checkbox: ui.checkbox
    r18_checkbox: ui.checkbox
    scroll_pixels_radio: ui.radio
    tiles_row: ui.row
    selected_tile: UiMetatile | None


    def __init__(self, parent: ui.element, background_tiles: list[UiMetatile]) -> None:
        self.parent = parent
        self.background_tiles = background_tiles
        self.selected_tile = None
        self.build_ui()
        self.initialized = True


    async def on_change_project_type(self, event: events.ValueChangeEventArguments[str]) -> None:
        if event.value != self.project_type and self.tiles_changed:
            with ui.dialog() as dialog, ui.card():
                ui.label('Changing project type will delete extra tiles. Are you sure?')
                with ui.row():
                    ui.button('Yes', on_click=lambda: dialog.submit(True))
                    ui.button('No', on_click=lambda: dialog.submit(False))
            result: bool = await dialog
        else:
            result = True
        if result:
            self.project_type = event.value
            enabled = bool(PROJECT_TYPES[self.project_type]['scrolling'])
            enable(self.r18_checkbox, enabled)
            enable(self.scroll_pixels_radio, enabled)
            ui.notify(f'Project type changed to {self.project_type}')


    def reserve_second_pattern_table(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        if event.value:
            self.available_tiles *= 2
        else:
            self.available_tiles //= 2
        if not self.r18_hardware_scroll:
            self.scrolling_tiles = self.available_tiles // (8 // self.scroll_pixels)
        else:
            self.scrolling_tiles = self.available_tiles
        ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
        self.scrolling_tiles_badge.set_text(str(self.scrolling_tiles))


    def set_105_color_mode(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        global FPS_OPTIONS
        enable(self.second_pattern_checkbox, not event.value)
        if event.value:
            self.fps += 1
            self.available_tiles //= 2
        else:
            self.fps -= 1
            self.available_tiles *= 2
        self.second_pattern_checkbox.value = event.value
        self.fps_badge.set_text(FPS_OPTIONS[self.fps])


    def detach_pattern_layers(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        if event.value:
            self.available_tiles *= 3
        else:
            self.available_tiles //= 3
        if not self.r18_hardware_scroll:
            self.scrolling_tiles = self.available_tiles // (8 // self.scroll_pixels)
        else:
            self.scrolling_tiles = self.available_tiles
        ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
        self.scrolling_tiles_badge.set_text(str(self.scrolling_tiles))


    def update_fps_badge(self) -> None:
        global FPS_OPTIONS
        with ui.row().classes('items-center gap-2 flex-nowrap'):
            ui.label('Frames per second:')
            self.fps_badge = ui.badge(FPS_OPTIONS[self.fps], color='magenta')
            if self.frame_rate != 'automatic':
                ui.label(f'({self.frame_rate})')


    def force_specific_frame_rate(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        global TARGET_OPTIONS
        if not event.value is None:
            enable(self.frame_rate_radio, event.value)
            self.frame_rate_badge.set_text(self.frame_rate_radio.value)
        self.target = TARGET_OPTIONS[1 if event.value else 0]
        self.frame_rate = self.frame_rate_radio.value
        self.target_badge.set_text(self.target)
        self.frame_rate_badge.visible = event.value
        ui.notify(f'Target platform set to {self.target}')


    def change_frame_rate(self, event: events.ValueChangeEventArguments[str]) -> None:
        self.frame_rate_badge.visible = True
        # todo: change to e.sender.value?
        self.frame_rate_badge.set_text(self.frame_rate_radio.value)


    def set_scroll_in_pixels(self, event: events.ValueChangeEventArguments[int]) -> None:
        if event.value != self.scroll_pixels and not self.r18_hardware_scroll:
            tmp = self.available_tiles // (8 // event.value)
            if self.scrolling_tiles != tmp:
                ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
            self.scrolling_tiles = tmp
            self.scroll_pixels = event.value
        self.scrolling_tiles_badge.set_text(str(self.scrolling_tiles))


    def allow_palette_change(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        global TARGET_OPTIONS
        if event.value:
            self.palette = event.value
        self.target = TARGET_OPTIONS[1 if event.value else 0]
        self.target_badge.set_text(self.target)
        ui.notify(f'Target platform set to {self.target}')


    def set_r18(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        """Use the V9938 VDP register R#18 to scroll horizontally."""
        global TARGET_OPTIONS
        if event.value:
            self.r18_hardware_scroll = event.value
            self.scrolling_tiles = self.available_tiles
        else:
            self.scrolling_tiles = self.available_tiles // (8 // self.scroll_pixels)
        self.target = TARGET_OPTIONS[1 if event.value else 0]
        self.target_badge.set_text(self.target)
        self.scrolling_tiles_badge.set_text(str(self.scrolling_tiles))
        ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
        ui.notify(f'Target platform set to {self.target}')


    def toggle_megarom(self, event: events.ClickEventArguments) -> None:
        pass


    def set_tile_style(self, element: ui.element, color: str = '#000000') -> ui.element:
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


    def select_tile(self, metatile: UiMetatile) -> UiMetatile:
        if self.selected_tile and not self.selected_tile is metatile:
            self.selected_tile.style('border: 1px solid #444; filter: brightness(100%);')
        self.selected_tile = metatile.style('border: 3px solid #444; filter: brightness(80%);')
        enable(self.tile_buttons, True)
        return self.selected_tile


    def on_select_tile(self, event: events.GenericEventArguments) -> None:
        if isinstance(event.sender, UiMetatile):
            self.select_tile(event.sender)


    def add_tile(self, bg_color: int) -> None:
        with self.tiles_row:
            tooltip = f'color #{bg_color} ({PALETTE[bg_color]})'
            self.background_tiles.append(
                self.select_tile(UiMetatile(Tile8x8(DEFAULT_FG_COLOR, bg_color))
                        .classes('no-select')
                        .on('mousedown', lambda e: self.on_select_tile(e)).tooltip(tooltip))
            )


    def on_add_tile(self, event: events.ClickEventArguments, index: int) -> None:
        self.add_tile(index)
        enable(self.tile_buttons, True)


    def draw_color_dropdown(self, palette: list[str]) -> None:
        with ui.dropdown_button('select color', auto_close=True):
            for index, color in enumerate(palette[1:], start=1):
                ui.item(f'color {index}', on_click=lambda e, i=index: self.on_add_tile(e, i)) \
                        .style(f'''
                            background-color: {color};
                            color: {get_text_color(color)};
                        ''').props(f'{color=}')


    async def on_edit_tile_clicked(self, event: events.ClickEventArguments) -> None:
        editor = None
        with ui.dialog() as dialog, ui.card().style('max-width: none;') as parent:
            if self.selected_tile:
                if self.selected_tile:
                    acopy = Tile8x8.copy(self.selected_tile.grid)
                    editor = TileEditor(parent, acopy)
            with ui.row().classes('w-full justify-end'):
                ui.button('OK', on_click=lambda: dialog.submit(True))
                ui.button('Cancel', on_click=lambda: dialog.submit(False))
        result = await dialog
        if result and editor and self.selected_tile:
            # return tile changes
            self.selected_tile.reload(editor.grid)


    def erase_tile(self, tile: UiMetatile) -> None:
        if self.selected_tile:
            self.tiles.remove(tile)
            self.selected_tile = None
        enable(self.tile_buttons, False)


    def on_erase_tile(self, event: events.ClickEventArguments) -> None:
        if self.selected_tile:
            self.erase_tile(self.selected_tile)


    def build_ui(self) -> None:
        with self.parent:
            toggle = ui.toggle({title:'' for title in PROJECT_TYPES.keys()}, value=self.project_type,
                    on_change=self.on_change_project_type)
            for i, key in enumerate(PROJECT_TYPES.keys(), start=1):
                with ui.teleport(f'#{toggle.html_id} > button:nth-child({i}) .q-btn__content'):
                    ui.icon(str(PROJECT_TYPES[key]['icon']), size='xl').tooltip(str(PROJECT_TYPES[key]['tooltip']))
            with ui.row().classes('items-center gap-2 flex-nowrap'):
                ui.label('Project type: ')
                ui.label().bind_text_from(toggle, 'value')

            header('Summary')
            with ui.column().classes('pl-8 gap-1 w-full'):
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Target platform:')
                    self.target_badge = ui.badge(self.target, color='blue')
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('ROM size:')
                    ui.badge('32K', color='green')
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Page size:')
                    ui.badge('16K', color='red')
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Amount of tiles available:')
                    self.scrolling_tiles_badge = ui.badge(str(self.available_tiles), color='orange')
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Frames per second:')
                    self.fps_badge = ui.badge(FPS_OPTIONS[self.fps], color='brown')
                    self.frame_rate_badge = ui.badge(self.frame_rate, color='brown')
                    self.frame_rate_badge.visible = self.force_frame_rate

            header('Settings')
            with ui.column().classes('pl-8 w-full'):
                header('Display engine')
                with ui.column().classes('ml-8'):
                    self.second_pattern_checkbox = ui.checkbox('Reserve second pattern table in VRAM for next frame',
                           on_change=self.reserve_second_pattern_table)
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('warning', color='warning').classes('text-xl')
                            ui.label('This option may double the required VRAM data transfer when updating tile patterns dinamically.')
                    ui.checkbox('105 color mode', on_change=self.set_105_color_mode)
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('warning', color='warning').classes('text-xl')
                            ui.label('This option reduces color clash but also reduces the game frame rate by half and may cause flicker.')
                    ui.checkbox('Detach pattern layers for each third of screen region',
                            on_change=self.detach_pattern_layers)
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('info', color='black').classes('text-xl')
                            ui.label('Select a distinct pattern table for each screen region if tiles are different in each region.')

                    header('MSX2 features')
                    with ui.column().classes('ml-8'):
                        ui.checkbox('Allow palette change', on_change=self.allow_palette_change)
                        self.r18_checkbox = ui.checkbox('R#18 hardware scroll', on_change=self.set_r18).disable()
                        with ui.column().classes('ml-8'):
                            with ui.row().classes('items-center flex-nowrap'):
                                ui.icon('info', color='black').classes('text-xl')
                                ui.label('This option will cause visible artifacts on the left and right edges of the screen.')

                        ui.checkbox('Force specific frame rate', on_change=self.force_specific_frame_rate)
                        with ui.column().classes('ml-8'):
                            self.frame_rate_radio = ui.radio(FRAME_RATE_OPTIONS, value=FRAME_RATE_OPTIONS[0],
                                    on_change=lambda e: self.change_frame_rate(e)).props('inline').disable()

                    header('Amount of pixels to scroll each frame')
                    with ui.column().classes('ml-8'):
                        self.scroll_pixels_radio = ui.radio([1, 2, 4, 8], value=8,
                                on_change=lambda e: self.set_scroll_in_pixels(e)).props('inline').disable()

                header('Static tiles')

                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Create tile by background color').classes('whitespace-nowrap')
                    self.draw_color_dropdown(PALETTE)

                with ui.row().classes('items-center flex-nowrap') as self.tile_buttons:
                    text = 'Edit selected tile'
                    ui.button(icon='fa-solid fa-edit',
                    on_click=lambda e: self.on_edit_tile_clicked(e)).tooltip(text)

                    text = 'Erase selected tile'
                    ui.button(icon='fa-solid fa-minus',
                    on_click=self.on_erase_tile).tooltip(text)

                    # background colour container
                    with ui.row().classes('items-center gap-2 px-2 min-w-[800px]') as self.tiles_row:
                        self.tiles_row.style(
                            f'''background-color: {CONTAINER_COLOR};
                                height: {TILE_STORAGE_HEIGHT}px;
                                overflow-y: auto;'''
                        )
                        ...

                    enable(self.tile_buttons, not self.selected_tile is None)


"""
                ui.label('Memory layout')
                with ui.column().classes('ml-8'):
                    ui.checkbox('ROM bank switching', on_change=lambda e: self.toggle_megarom(e))
                    with ui.column().classes('ml-8'):
                        ui.radio(ROM_OPTIONS, value=ROM_OPTIONS[0],
                                on_change=lambda e: self.change_frame_rate(e)).props('inline').disable()
                                """


if __name__ in {"__main__", "__mp_main__"}:
    alist: list[UiMetatile] = []
    Project(ui.column().classes('w-full min-h-screen p-0 m-0'), alist)
    from common import run
    run()
