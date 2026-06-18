import json

from typing import Callable
from functools import partial
from nicegui import ui, events
from constants import GRID_PIXEL_SIZE, GRID_PIXEL_MAX, GRID_PIXEL_MIN
from common import header, get_text_color, menu_item
from v9918 import Tile8x8, TILE_SIZE, DEFAULT_FG_COLOR, DEFAULT_BG_COLOR, PALETTE, divide_colors


# constants
GRID_FG_LAYER_SIZE = 16        # size of foreground color pixel
COPY_TO_CLIPBOARD_FORMATS = {
    'index' : {
        'icon': 'fa-solid fa-table-cells-large',
        'tooltip': 'export tile index for the MSX'
    },
    'rgb' : {
        'icon': 'fa-solid fa-palette',
        'tooltip': 'export tile as RGB values'
    }
}

# toggle mode: switches between paintbrush and eraser automatically by context
TOGGLE_MODE = False
DEACTIVATE, ACTIVATE, OFF = 0, 1, 2

# Common settings
toggle_mode_status = OFF

# functions
async def show_message_dialog(message: str) -> str:
    with ui.dialog() as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit('OK'))
    return str(await dialog)


async def show_confirm_dialog(message: str) -> str:
    with ui.dialog() as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button('YES', on_click=lambda: dialog.submit('yes'))
            ui.button('NO', on_click=lambda: dialog.submit('no'))
    return str(await dialog)


class UiPixel(ui.card):
    value: bool = False
    fg: int = DEFAULT_FG_COLOR
    bg: int = DEFAULT_BG_COLOR
    initialized: bool = False

    # ui elements
    inner: ui.card

    def __init__(self, value: bool, combined: int | None = None, fg: int | None = None, bg: int | None = None, scale: int | None = None):
        super().__init__()
        with self:
            # Just set values before initializing
            self.set_value(value)
            self.set_colors(combined, fg, bg)
            self.set_scale(scale)
            self.initialized = True
            self.build_ui()


    def set_value(self, value: bool) -> None:
        self.value = value


    def set_colors(self, combined: int | None = None, fg: int | None = None, bg: int | None = None) -> None:
        if combined:
            self.fg, self.bg = divide_colors(combined)
        else:
            if not fg is None:
                self.fg = fg
            if not bg is None:
                self.bg = bg
        if self.initialized:
            self.repaint(False)


    def set_scale(self, scale: int | None = None, repaint: bool = False) -> None:
        if scale:
            self.scale = scale
        else:
            self.scale = GRID_PIXEL_SIZE
        if self.initialized and repaint:
            self.repaint(False)


    def set(self, value: bool, combined: int | None = None, fg: int | None = None, bg: int | None = None) -> None:
        self.set_value(value)
        self.set_colors(combined, fg, bg)


    def repaint(self, background_occlusion: bool) -> None:
        # if pixel is active, use foreground color, otherwise use background color
        index = self.fg if self.value else self.bg
        # grid gets poluted when scale is too small
        background_occlusion = self.scale < 8 or background_occlusion
        self.style(f'''
            box-shadow: none;
            width: {self.scale}px;
            height: {self.scale}px;
            background-image: none;
            background-color: {PALETTE[index if background_occlusion else self.bg]};
            border: 0px;
            border-radius: 0;
            cursor: pointer;
        ''')
        if self.bg == 0:
            self.style(f'''
                background-image: url('static/color0.png');
                background-size: 100% 100%;
                background-repeat: no-repeat;
                background-position: center;
                image-rendering: pixelated;
                image-rendering: crisp-edges;
            ''')
        self.inner.style(f'''
            width: {2/3 * self.scale}px;
            height: {2/3 * self.scale}px;
            background-image: none;
            background-color: {PALETTE[index]};
            border: 1px solid {PALETTE[self.fg]};
            visibility: {'hidden' if background_occlusion else 'visible'};
            border-radius: 0;
            cursor: pointer;
        ''')
        if self.fg == 0:
            self.inner.style(f'''
                border: 1px dashed {get_text_color(PALETTE[self.bg])};
                background-image: url('static/color0.png');
                background-size: 100% 100%;
                background-repeat: no-repeat;
                background-position: center;
                image-rendering: pixelated;
                image-rendering: crisp-edges;
            ''')


    def build_ui(self) -> None:
        with self.tight().style('display: flex; justify-content: center; align-items: center;'):
            self.inner = ui.card().tight().classes('items-center justify-center')
        self.repaint(False)


class ColorButton(ui.button):
    label: str | None
    color: str

    def __init__(self, color: str, label: str = '', on_click: Callable[[events.ClickEventArguments], None] | None = None):
        super().__init__(label, color=None if color == 'transparent' else color, on_click=on_click)
        self.label = label
        self.color = color
        self.build_ui()


    def build_ui(self) -> None:
        self.style(f'''
            border: 2px solid #444;
            width: 30px;
            height: 30px;
            overflow: hidden;
        ''')
        if self.color == 'transparent':
            self.style(f'''
                border: 2px dashed #444;
                background-image: url('static/color0.png');
                background-size: 100% 100%;
                background-repeat: no-repeat;
                background-position: center;
                image-rendering: pixelated;
                image-rendering: crisp-edges;
            ''')
        self.tooltip(self.color).props(f'text-color={get_text_color(self.color)}')


class TileEditor(ui.element):
    current_fg_color: int = DEFAULT_FG_COLOR
    current_bg_color: int = DEFAULT_BG_COLOR
    last_fg_button: ColorButton
    last_bg_button: ColorButton
    last_tool_button: ui.button
    # combined brush
    dragging: bool = False
    dragging_on_pixel: bool = False
    # display confirmation dialog when erasing pattern
    confirm_erasing: bool = True
    # hide background colour when pixel is visible and foreground colour when it's not
    background_occlusion: bool = False
    # data has changed and need saving?
    dirty: bool = False
    # control mouse dragging
    old_x: int | None = None
    old_y: int | None = None

    # ui elements
    patternbrush: ui.button
    colorbrush: ui.button
    eraser: ui.button
    inverter: ui.button

    def __init__(self, parent: ui.element, grid: Tile8x8 | object | None = None, fg: int | None = None, bg: int | None = None):
        super().__init__('div')
        self.parent = parent

        # selected colours from palette
        if fg:
            self.current_fg_color = fg
        if bg:
            self.current_bg_color = bg

        # UI elements to remember
        if not grid:
            self.grid = Tile8x8(self.current_fg_color, self.current_bg_color)
        elif isinstance(grid, Tile8x8):
            self.grid = grid
        else:
            self.grid = json.load(grid) # type: ignore

        # define editor title
        width = len(self.grid[0])
        height = len(self.grid)
        self.title = f'{width}x{height} Tile'

        self.set_pixel_function = self.grid.set_pattern
        self.pixel_refs: list[list[UiPixel]] = []
        self.bg_color_refs: list[list[ui.element]] = []
        self.fg_color_refs: list[list[ui.element]] = []

        self.build_ui()


    def build_ui(self) -> None:
        with self.parent:
            with ui.row().classes('items-center flex-nowrap'):
                with ui.button(icon='menu'):
                    with ui.menu().props('auto-close'):
                        with ui.column():
                            with ui.column().classes('items-center w-full'):
                                menu_item(ui.label('Copy to clipboard as')).classes('mt-4')
                                self.clipboard_toggle = ui.toggle({title:'' for title in COPY_TO_CLIPBOARD_FORMATS.keys()},
                                        value='index', on_change=self.on_set_copy_format)
                                for i, key in enumerate(COPY_TO_CLIPBOARD_FORMATS.keys(), start=1):
                                    with ui.teleport(f'#{self.clipboard_toggle.html_id} > button:nth-child({i}) .q-btn__content ') as div:
                                        with ui.element('div').tooltip(COPY_TO_CLIPBOARD_FORMATS[key]['tooltip']).classes('flex items-center gap-2'):
                                            ui.icon(COPY_TO_CLIPBOARD_FORMATS[key]['icon'])
                                            ui.label(key)

                            text = 'display confirmation dialog before erasing the tile'
                            menu_item(ui.switch('Confirm before erasing', value=self.confirm_erasing,
                                      on_change=self.toggle_confirm_erasing)).tooltip(text)
                            text = 'hide background pixel when foreground pixel is visible'
                            menu_item(ui.switch('Activate background occlusion', value=self.background_occlusion,
                                      on_change=self.toggle_background_occlusion)).tooltip(text)
                if self.title:
                    header(self.title)
                else:
                    header(f'{TILE_SIZE}x{TILE_SIZE} Tile Editor')

            with ui.row().classes('items-start gap-8'):
                self.build_tools()
                self.build_grid()
                self.build_palette()


    def build_tools(self) -> None:
        with ui.column().classes('gap-1'):
            header('Tools')

            with ui.row().classes('gap-2 flex-wrap max-w-[180px]'):
                # outline default tool
                text = '''combined brush
                    left click on background pixel: change foreground colour and set pixel
                    left click on foreground pixel: unset pixel only
                    right click: change background colour line'''
                self.combinedbrush = ui.button(icon='fa-solid fa-magic fa-lg', on_click=self.on_select_tool).tooltip(text).props('outline')
                self.last_tool_button = self.combinedbrush

                text = '''pattern brush
                    left click: set pixel
                    right click: unset pixel'''
                self.patternbrush = ui.button(icon='fa-solid fa-pencil fa-lg', on_click=self.on_select_tool).tooltip(text)

                text = '''color brush
                    left click: set foreground colour in the same line to the selected foreground colour
                    right click: set background colour in the same line to the selected background colour'''
                self.colorbrush = ui.button(icon='fa-solid fa-brush fa-lg', on_click=self.on_select_tool).tooltip(text)

                text = '''eraser
                    left click: unset pixel'''
                self.eraser = ui.button(icon='fa-solid fa-eraser fa-lg', on_click=self.on_select_tool).tooltip(text)
                self.eraser.visible = not TOGGLE_MODE

                text = '''inverter
                    switch foreground and background colours and invert pattern in a single line (non destructable)'''
                self.inverter = ui.button(icon='fa-solid fa-wand-magic-sparkles fa-lg', on_click=self.on_select_tool).tooltip(text)

                ui.separator()

                text = 'shift tile left'
                ui.button(icon='fa-solid fa-arrow-left fa-lg', on_click=self.shift_left).props('color=black').tooltip(text)

                text = 'shift tile right'
                ui.button(icon='fa-solid fa-arrow-right fa-lg', on_click=self.shift_right).props('color=black').tooltip(text)

                text = 'shift tile up'
                ui.button(icon='fa-solid fa-arrow-up fa-lg', on_click=self.shift_up).props('color=black').tooltip(text)

                text = 'shift tile down'
                ui.button(icon='fa-solid fa-arrow-down fa-lg', on_click=self.shift_down).props('color=black').tooltip(text)

                text = 'mirror horizontally (non destructable)'
                ui.button(icon='fa-solid fa-arrows-left-right fa-lg', on_click=self.mirror_tile_horizontally).props('color=black').tooltip(text)

                text = 'mirror vertically (non destructable)'
                ui.button(icon='fa-solid fa-arrows-up-down fa-lg', on_click=self.mirror_tile_vertically).props('color=black').tooltip(text)

                ui.separator()

                ui.button(icon='fa-solid fa-copy fa-lg', on_click=self.on_copy_to_clipboard).props('color=green').tooltip('copy pattern to clipboard')
                ui.button(icon='fa-solid fa-trash fa-lg', on_click=self.on_clear_tile).props('color=red').tooltip('erase tile completely')


    def build_grid(self) -> None:
        with ui.column().classes('gap-1'):
            with ui.row().classes('gap-1'):

                with ui.column():
                    ui.label('Grid').classes('text-lg font-semibold')
                    with ui.column().classes('gap-0 min-w-[250px] items-center').style('height: 250px;'):
                        ui.slider(min=GRID_PIXEL_MIN, max=GRID_PIXEL_MAX, value=GRID_PIXEL_SIZE) \
                                .on('update:model-value', lambda e: self.on_update_scale_slider(e),
                                    leading_events=False, throttle=0)
                        for y in range(TILE_SIZE):
                            row_refs: list[UiPixel] = []
                            with ui.row().classes('gap-0'):
                                for x in range(TILE_SIZE):
                                    pixel = UiPixel(False, self.grid[y].get_combined())
                                    pixel.on('mousedown', lambda e, px=x, py=y: self.on_drag_on_grid(e, px, py))
                                    pixel.on('mouseover', lambda e, px=x, py=y: self.on_drag_on_grid(e, px, py))
                                    pixel.on('contextmenu.prevent', lambda: None)
                                    row_refs.append(pixel)
                            self.pixel_refs.append(row_refs)


    def set_scale(self, value: int) -> None:
        for y in range(TILE_SIZE):
            for x in range(TILE_SIZE):
                self.pixel_refs[y][x].set_scale(value)
        self.repaint()


    def on_update_scale_slider(self, e: events.GenericEventArguments) -> None:
        self.set_scale(e.args)


    def get_colorbutton_label(self, index: int) -> str:
        n = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
        return ['', 'F', 'B', 'FB'][n]


    def build_palette(self) -> None:
        with ui.column().classes('gap-4 min-w-[260px]'):
            header('Palette')

            with ui.row().classes('gap-2 flex-wrap max-w-[180px]'):
                for index, color in enumerate(PALETTE):
                    sel = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
                    # chicungunha
                    button = ColorButton('transparent' if index == 0 else color, self.get_colorbutton_label(index),
                                    on_click=partial(self.on_select_fg_color, index=index)) \
                            .on('contextmenu.prevent', partial(self.on_select_bg_color, index=index))
                    if sel & 1: self.last_fg_button = button
                    if sel & 2: self.last_bg_button = button


    def toggle_confirm_erasing(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        if event.value is not None:
            self.confirm_erasing = event.value


    def toggle_background_occlusion(self, event: events.ValueChangeEventArguments[bool | None]) -> None:
        if event.value is not None:
            self.background_occlusion = event.value
            self.repaint()


    def select_tool(self, sender: ui.element) -> None:
        if self.last_tool_button:
            self.last_tool_button._props.pop('outline', None)
        sender.props('outline')
        if isinstance(sender, ui.button):
            self.last_tool_button = sender


    def on_select_tool(self, event: events.ClickEventArguments) -> None:
        self.select_tool(event.sender)


    def on_select_fg_color(self, event: events.ClickEventArguments, index: int) -> None:
        tmp = self.current_fg_color
        self.current_fg_color = index
        if self.last_fg_button:
            self.last_fg_button.set_text(self.get_colorbutton_label(tmp))
        if isinstance(event.sender, ColorButton):
            event.sender.set_text(self.get_colorbutton_label(index))
            self.last_fg_button = event.sender


    def on_select_bg_color(self, event: events.GenericEventArguments, index: int) -> None:
        tmp = self.current_bg_color
        self.current_bg_color = index
        if self.last_bg_button != event.sender:
            self.last_bg_button.set_text(self.get_colorbutton_label(tmp))
        if isinstance(event.sender, ColorButton):
            event.sender.set_text(self.get_colorbutton_label(index))
            self.last_bg_button = event.sender


    def repaint(self) -> None:
        for y in range(TILE_SIZE):
            for x in range(TILE_SIZE):
                value = bool(self.grid[y].get_pixel(x))
                combined = self.grid[y].get_combined()
                self.pixel_refs[y][x].set(value, combined=combined)
                self.pixel_refs[y][x].repaint(self.background_occlusion)


    def unpaint(self, x: int, y: int) -> None:
        self.grid.unset_pattern(x, y)
        self.pixel_refs[y][x].set_value(False)


    def paint(self, x: int, y: int) -> None:
        self.grid.set_pattern(x, y)
        self.pixel_refs[y][x].set_value(True)


    def paint_fg(self, index: int, x: int, y: int) -> None:
        self.grid.set_fg(y, index)


    def paint_bg(self, index: int, x: int, y: int) -> None:
        self.grid.set_bg(y, index)


    def drag_combinedbrush(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            if not self.dragging:
                self.dragging = True
                self.dragging_on_pixel = bool(self.grid[y].get_pixel(x))
            if self.dragging_on_pixel:
                self.grid[y].unset_pattern(x)
                self.grid[y].set_fg(self.current_fg_color)
                self.repaint()
            else:
                self.pixel_refs[y][x].set_value(True)
                self.grid[y].set_pattern(x)
                self.grid[y].set_fg(self.current_fg_color)
                self.repaint()
        elif buttons == 2:
            self.grid[y].set_bg(self.current_bg_color)
            self.repaint()
        else:
            self.dragging = False
            self.dragging_on_pixel = False


    def drag_patternbrush(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint(x, y)
        elif buttons == 2:
            self.unpaint(x, y)
        self.repaint()


    def drag_colorbrush(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint_fg(self.current_fg_color, x, y)
        elif buttons == 2:
            self.paint_bg(self.current_bg_color, x, y)
        self.repaint()


    def drag_erase(self, buttons: int, x: int, y: int) -> None:
        self.unpaint(x, y)
        self.repaint()


    async def on_drag_on_grid(self, event: events.GenericEventArguments, x: int, y:int) -> None:
        # discard mouseover when no button is pressed
        buttons = event.args.get('buttons', 0)
        # button was released
        if buttons == 0:
            self.dragging = False
            return
        # nothing to update
        if self.old_x == x and self.old_y == y:
            return
        self.old_x, self.old_y, self.dirty = x, y, True
        if self.last_tool_button is self.combinedbrush:
            return self.drag_combinedbrush(buttons, x, y)
        if self.last_tool_button is self.patternbrush:
            return self.drag_patternbrush(buttons, x, y)
        if self.last_tool_button is self.colorbrush:
            print('colorbrush!')
            return self.drag_colorbrush(buttons, x, y)
        if self.last_tool_button is self.eraser:
            return self.drag_erase(buttons, x, y)
        if self.last_tool_button is self.inverter:
            return self.invert_line(y)
        await show_message_dialog('Not implemented yet.')


    def invert_line(self, y: int) -> None:
        fg, bg = self.grid.get_fg(y), self.grid.get_bg(y)
        self.grid[y].set_fg(bg)
        self.grid[y].set_bg(fg)
        self.grid[y].pattern = 0xff & ~self.grid[y].pattern
        self.repaint()


    async def on_clear_tile(self) -> None:
        result = await show_confirm_dialog('Are you sure you want to delete the tile?') \
                if self.confirm_erasing and self.dirty else 'yes'
        if result == 'yes':
            for y in range(TILE_SIZE):
                self.grid.set_fg(y, self.current_fg_color)
                self.grid.set_bg(y, self.current_bg_color)
                for x in range(TILE_SIZE):
                    self.grid.unset_pattern(x, y)
            self.repaint()
            self.dirty = False


    def on_set_copy_format(self, event: events.ValueChangeEventArguments[str]) -> None:
        self.grid.set_copy_format(event.value)


    def on_copy_to_clipboard(self, event: events.ClickEventArguments) -> None:
        script = f'''navigator.clipboard.writeText("{self.grid}")'''
        ui.run_javascript(script)


    def shift_left(self) -> None:
        self.grid.shift_left()
        self.repaint()


    def shift_right(self) -> None:
        self.grid.shift_right()
        self.repaint()


    def shift_up(self) -> None:
        self.grid.shift_up()
        self.repaint()


    def shift_down(self) -> None:
        self.grid.shift_down()
        self.repaint()


    def mirror_tile_horizontally(self) -> None:
        self.grid.mirror_horizontally()
        self.repaint()


    def mirror_tile_vertically(self) -> None:
        self.grid.mirror_vertically()
        self.repaint()


if __name__ in {"__main__", "__mp_main__"}:
    with ui.row():
        TileEditor(parent=ui.column().classes('w-full min-h-screen p-0 m-0'))
    from common import run
    run()
