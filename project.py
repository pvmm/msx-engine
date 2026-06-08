from nicegui import ui, events
from tileeditor import TileEditor
from stageeditor import StageEditor
from common import header, get_text_color, menu_item
from constants import TILE_STORAGE_HEIGHT


# constants
PROJECT_TYPES = ['static screen', 'automatic R2L scrolling', 'free side scrolling']
TARGET_OPTIONS = ['MSX1', 'MSX2 or above']
FRAME_RATE_OPTIONS = ['60Hz', '50Hz']
ROM_OPTIONS = ['8K', '16K']
FPS_OPTIONS = ['frame rate', 'half the frame rate', 'quarter the frame rate']


class Project:
    # settings
    target = TARGET_OPTIONS[0]
    available_tiles = 256
    scrolling_tiles = available_tiles
    palette = False
    r18_hardware_scroll = False
    megarom = False
    force_frame_rate = False
    frame_rate = FRAME_RATE_OPTIONS[0]
    rom_type = ROM_OPTIONS[0]
    _105_color_mode = False
    fps = FPS_OPTIONS.index('frame rate')
    scroll_pixels = 8
    project_type = PROJECT_TYPES[0]
    project_changed = True
    tiles_changed = False

    # ui elements
    scrolling_tiles_badge = None
    frame_rate_badge = None
    frame_rate_radio = None
    fps_badge = None
    target_badge = None
    second_pattern_checkbox = None
    r18_checkbox = None
    scroll_pixels_radio = None

    def __init__(self, parent):
        self.parent = parent
        self.build_ui()

    async def change_project_type(self, e: events.ValueChangeEventArguments) -> None:
        if e.value != self.project_type and self.tiles_changed:
            with ui.dialog() as dialog, ui.card():
                ui.label('Changing project type will delete extra tiles. Are you sure?')
                with ui.row():
                    ui.button('Yes', on_click=lambda: dialog.submit(True))
                    ui.button('No', on_click=lambda: dialog.submit(False))
            result = await dialog
        elif not self.tiles_changed:
            result = True
        if result:
            self.project_type = e.value
            if self.project_type != 'static screen':
                self.r18_checkbox.enable()
                self.scroll_pixels_radio.enable()
            else:
                self.r18_checkbox.disable()
                self.scroll_pixels_radio.disable()
            ui.notify(f'Project type changed to {self.project_type}')
        else:
            e.sender.set_value(self.project_type)


    def reserve_second_pattern_table(self, e) -> None:
        print('e',e)
        if e.value:
            self.available_tiles *= 2
        else:
            self.available_tiles //= 2
        if not self.r18_hardware_scroll:
            scrolling_tiles = self.available_tiles // (8 // self.scroll_pixels)
        else:
            scrolling_tiles = self.available_tiles
        ui.notify(f'Amount of tiles available: {scrolling_tiles}')
        self.scrolling_tiles_badge.set_text(scrolling_tiles)


    def set_105_color_mode(self, e) -> None:
        global FPS_OPTIONS
        if e.value:
            self.fps += 1
            self.second_pattern_checkbox.disable()
            self.available_tiles //= 2
        else:
            self.fps -= 1
            self.second_pattern_checkbox.enable()
            self.available_tiles *= 2
        self.second_pattern_checkbox.value = e.value
        self.fps_badge.set_text(FPS_OPTIONS[self.fps])


    def detach_pattern_layers(self, e) -> None:
        if e.value:
            self.available_tiles *= 3
        else:
            self.available_tiles //= 3
        if not self.r18_hardware_scroll:
            self.scrolling_tiles = self.available_tiles // (8 // self.scroll_pixels)
        else:
            self.scrolling_tiles = self.available_tiles
        ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
        self.scrolling_tiles_badge.set_text(self.scrolling_tiles)


    def update_fps_badge(self) -> None:
        global FPS_OPTIONS
        with ui.row().classes('items-center gap-2 flex-nowrap'):
            ui.label('Frames per second:')
            self.fps_badge = ui.badge(FPS_OPTIONS[self.fps], color='magenta')
            if self.frame_rate != 'automatic':
                ui.label(f'({self.frame_rate})')


    def force_specific_frame_rate(self, e) -> None:
        global TARGET_OPTIONS
        if e.value:
            self.frame_rate_badge.set_text(self.frame_rate_radio.value)
            self.frame_rate_radio.enable()
        else:
            self.frame_rate_radio.disable()
        self.target = TARGET_OPTIONS[1 if e.value else 0]
        self.frame_rate = self.frame_rate_radio.value
        self.target_badge.set_text(self.target)
        self.frame_rate_badge.visible = e.value
        ui.notify(f'Target platform set to {self.target}')


    def change_frame_rate(self, e) -> None:
        self.frame_rate_badge.visible = True
        # todo: change to e.sender.value?
        self.frame_rate_badge.set_text(self.frame_rate_radio.value)


    def set_scroll_in_pixels(self, e) -> None:
        if e.value != self.scroll_pixels and not self.r18_hardware_scroll:
            tmp = self.available_tiles // (8 // e.value)
            if self.scrolling_tiles != tmp:
                ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
            self.scrolling_tiles = tmp
            self.scroll_pixels = e.value
        self.scrolling_tiles_badge.set_text(self.scrolling_tiles)


    def allow_palette_change(self, e) -> None:
        global TARGET_OPTIONS
        self.palette = e.value
        self.target = TARGET_OPTIONS[1 if e.value else 0]
        self.target_badge.set_text(self.target)
        ui.notify(f'Target platform set to {self.target}')


    def set_r18(self, e) -> None:
        global TARGET_OPTIONS
        self.r18_hardware_scroll = e.value
        if e.value:
            self.scrolling_tiles = self.available_tiles
        else:
            self.scrolling_tiles = self.available_tiles // (8 // self.scroll_pixels)
        self.target = TARGET_OPTIONS[1 if e.value else 0]
        self.target_badge.set_text(self.target)
        self.scrolling_tiles_badge.set_text(self.scrolling_tiles)
        ui.notify(f'Amount of tiles available: {self.scrolling_tiles}')
        ui.notify(f'Target platform set to {self.target}')


    def toggle_megarom(self, e) -> None:
        pass


    def add_background_tile(self, event) -> None:
        self.bg_color = event.sender._props.get('color')


    def draw_color_dropdown(self, palette) -> None:
        with ui.dropdown_button('select color', auto_close=True):
            for index, color in enumerate(self.palette[1:], start=1):
                ui.item(f'color {index}', on_click=lambda e: add_background_tile(e)) \
                        .style(f'''
                            background-color: {color};
                            color: {get_text_color(color)};
                        ''').props(f'{color=}')


    def build_ui(self) -> None:
        with self.parent:
            toggle = ui.toggle({x:'' for x in PROJECT_TYPES}, value=self.project_type, on_change=lambda e: self.change_project_type(e))
            with ui.teleport(f'#{toggle.html_id} > button:nth-child(1) .q-btn__content'):
                ui.icon('check_box_outline_blank', size='xl')
            with ui.teleport(f'#{toggle.html_id} > button:nth-child(2) .q-btn__content'):
                ui.icon('trending_flat', size='xl')
            with ui.teleport(f'#{toggle.html_id} > button:nth-child(3) .q-btn__content'):
                ui.icon('swap_horiz', size='xl')
            with ui.row().classes('items-center gap-2 flex-nowrap'):
                ui.label('Project type: ')
                ui.label().bind_text_from(toggle, 'value')

            header('Summary')
            with ui.column().classes('ml-8 gap-1'):
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
                    self.scrolling_tiles_badge = ui.badge(self.available_tiles, color='orange')
                with ui.row().classes('items-center flex-nowrap'):
                    ui.label('Frames per second:')
                    self.fps_badge = ui.badge(FPS_OPTIONS[self.fps], color='brown')
                    self.frame_rate_badge = ui.badge(self.frame_rate, color='brown')
                    self.frame_rate_badge.visible = self.force_frame_rate

            header('Settings')
            with ui.column().classes('ml-8'):
                header('Display engine')
                with ui.column().classes('ml-8'):
                    self.second_pattern_checkbox = ui.checkbox('Reserve second pattern table in VRAM for next frame',
                           on_change=lambda e: self.reserve_second_pattern_table(e))
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('warning', color='warning').classes('text-xl')
                            ui.label('This option may double the required VRAM data transfer when updating tile patterns dinamically.')
                    ui.checkbox('105 color mode', on_change=lambda e: self.set_105_color_mode(e))
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('warning', color='warning').classes('text-xl')
                            ui.label('This option reduces color clash but also reduces the game frame rate by half and may cause flicker.')
                    ui.checkbox('Detach pattern layers for each third of screen region',
                            on_change=lambda e: self.detach_pattern_layers(e))
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('info', color='black').classes('text-xl')
                            ui.label('Select a distinct pattern table for each screen region if tiles are different in each region.')

                    header('MSX2 features')
                    with ui.column().classes('ml-8'):
                        ui.checkbox('Allow palette change', on_change=lambda e: self.allow_palette_change(e))
                        r18_checkbox = ui.checkbox('R#18 hardware scroll', on_change=lambda e: self.set_r18(e)).disable()
                        with ui.column().classes('ml-8'):
                            with ui.row().classes('items-center flex-nowrap'):
                                ui.icon('info', color='black').classes('text-xl')
                                ui.label('This option will cause visible artifacts on the left and right edges of the screen.')

                        ui.checkbox('Force specific frame rate', on_change=lambda e: self.force_specific_frame_rate(e))
                        with ui.column().classes('ml-8'):
                            self.frame_rate_radio = ui.radio(FRAME_RATE_OPTIONS, value=FRAME_RATE_OPTIONS[0],
                                    on_change=lambda e: self.change_frame_rate(e)).props('inline').disable()

                    header('Amount of pixels to scroll each frame')
                    with ui.column().classes('ml-8'):
                        self.scroll_pixels_radio = ui.radio([1, 2, 4, 8], value=8,
                                on_change=lambda e: self.set_scroll_in_pixels(e)).props('inline').disable()

                ui.label('Memory layout')
                with ui.column().classes('ml-8'):
                    ui.checkbox('ROM bank switching', on_change=lambda e: self.toggle_megarom(e))
                    with ui.column().classes('ml-8'):
                        ui.radio(ROM_OPTIONS, value=ROM_OPTIONS[0],
                                on_change=lambda e: self.change_frame_rate(e)).props('inline').disable()


if __name__ in {"__main__", "__mp_main__"}:
    a = 1 / 0
    with ui.row():
        Project(ui.column().classes('w-full'))
    from common import run
    run()
