import json

from nicegui import ui, events
from typing import List, Tuple

from constants import GRID_PIXEL_SIZE
from common import header, get_text_color, menu_item
from v9918 import Tile8x8, TILE_SIZE, DEFAULT_FG_COLOR, DEFAULT_BG_COLOR, PALETTE, select_fg, select_bg, divide_colors

# constants
GRID_FG_LAYER_SIZE = 16        # size of foreground color pixel
COPY_TO_CLIPBOARD_FORMATS = ['index', 'rgb']

# toggle mode: switches between paintbrush and eraser automatically by context
TOGGLE_MODE = False
DEACTIVATE, ACTIVATE, OFF = 0, 1, 2

# Common settings
toggle_mode_status = OFF

# functions
async def show_message_dialog(message):
    with ui.dialog() as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit('OK'))
    result = await dialog


async def show_confirm_dialog(message):
    with ui.dialog() as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button('YES', on_click=lambda: dialog.submit('yes'))
            ui.button('NO', on_click=lambda: dialog.submit('no'))
    return await dialog


class PixelElement(ui.card):
    value: bool = False
    fg: int = DEFAULT_FG_COLOR
    bg: int = DEFAULT_BG_COLOR
    initialized: bool = False

    # ui elements
    inner = None

    def __init__(self, value: bool, combined: int = None, fg: int = None, bg: int = None, scale: int = None, **kwargs):
        super().__init__(**kwargs)
        self.set_value(value)
        self.set_colors(combined, fg, bg)
        self.set_scale(scale)
        self.initialized = True
        self.build_ui()


    def set_value(self, value: bool):
        self.value = value


    def set_colors(self, combined: int = None, fg: int = None, bg: int = None) -> None:
        if combined:
            self.fg, self.bg = divide_colors(combined)
        else:
            if fg:
                self.fg = fg
            if bg:
                self.bg = bg
        if self.initialized:
            self.repaint()


    def set_scale(self, scale: int = None) -> None:
        if scale:
            self.scale = scale
        else:
            self.scale = GRID_PIXEL_SIZE
        if self.initialized:
            self.repaint()


    def repaint(self) -> None:
        self.repaint_fg()
        self.repaint_bg()


    def repaint_fg(self) -> None:
        self.inner.style(
            f'''
            width: {self.scale - 8}px;
            height: {self.scale - 8}px;
            background-color: {PALETTE[self.fg] if self.value else PALETTE[self.bg]};
            border: 1px solid {PALETTE[self.fg]};
            border-radius: 0;
            cursor: pointer;
            '''
        )


    def repaint_bg(self) -> None:
        self.style(
            f'''
            width: {self.scale}px;
            height: {self.scale}px;
            background-color: {PALETTE[self.bg]};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )


    def build_ui(self):
        with self.tight().style('display: flex; justify-content: center; align-items: center;'):
            self.inner = ui.card().tight().classes('items-center justify-center')
        self.repaint()


class TileEditor(ui.element):
    current_fg_color = DEFAULT_FG_COLOR
    current_bg_color = DEFAULT_BG_COLOR
    last_fg_button = None
    last_bg_button = None
    last_tool_button = None
    # display dialog when erasing pattern?
    confirm_erasing = True
    # hide background colour when pixel is visible and foreground colour when it's not?
    background_occlusion = False
    # data has changed and need saving?
    dirty = False

    # ui elements
    patternbrush = None
    colorbrush = None
    eraser = None
    inverter = None

    def __init__(self, parent: ui.element, grid: List[List[int]] = None, fg: int = None, bg: int = None, **kwargs):
        super().__init__('div', **kwargs) 
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
            self.grid = json.load(grid)

        # define editor title
        width = len(self.grid[0])
        height = len(self.grid)
        self.title = f'{width}x{height} Tile'

        self.set_pixel_function = self.grid.set_pattern
        self.pixel_refs: List[List[ui.element]] = []
        self.bg_color_refs: List[List[ui.element]] = []
        self.fg_color_refs: List[List[ui.element]] = []

        self.build_ui()


    def build_ui(self) -> None:
        with self.parent:
            with ui.row().classes('items-center flex-nowrap'):
                with ui.button(icon='menu'):
                    with ui.menu().props('auto-close'):
                        with ui.column():
                            with ui.column().classes('items-center'):
                                menu_item(ui.label('Copy to clipboard as')).classes('mt-4')
                                self.clipboard_toggle = ui.toggle(COPY_TO_CLIPBOARD_FORMATS, value='index', on_change=self.on_set_copy_format)
                            text = 'display dialog when erasing pattern?'
                            menu_item(ui.switch('Confirm before erasing', value=self.confirm_erasing,
                                      on_change=self.toggle_confirm_erasing)).tooltip(text)
                            text = 'hide background colour when pixel is visible and foreground colour when it\'s not?'
                            menu_item(ui.switch('Display resulting pixel only', value=self.background_occlusion,
                                      on_change=self.toggle_background_occlusion)).tooltip(text)
                if self.title:
                    header(self.title)
                else:
                    header(f'{TILE_SIZE}x{TILE_SIZE} Tile Editor')

            with ui.row().classes('items-start gap-8'):
                self.build_tools()
                self.build_grid()
                self.build_sidebar()


    def build_tools(self) -> None:
        with ui.column().classes('gap-1'):
            header('Tools')

            with ui.row().classes('gap-2 flex-wrap max-w-[203px]'):
                # outline default tool
                text = 'combined brush\nleft click: change foreground colour and set pixel\nright click: change background colour line'
                self.combinedbrush = ui.button(icon='fa-solid fa-magic',
                    on_click=self.on_toggle_tool).tooltip(text).props('outline')
                self.last_tool_button = self.combinedbrush

                text = 'pattern brush\nleft click: set pixel\nright click: unset pixel'
                self.patternbrush = ui.button(icon='fa-solid fa-pencil',
                    on_click=self.on_toggle_tool).tooltip(text)

                text = 'color brush\nleft click: set foreground colour in the line to selected foreground colour\nright click: set background colour in the line to selected background colour'
                self.colorbrush = ui.button(icon='fa-solid fa-palette',
                    on_click=self.on_toggle_tool).tooltip(text)

                self.eraser = ui.button(icon='fa-solid fa-eraser',
                    on_click=self.on_toggle_tool).tooltip('eraser')
                self.eraser.visible = not TOGGLE_MODE

                text = 'inverter\nswitch foreground and background colors and invert pattern in a single line (non destructable)'
                ui.button(icon='fa-solid fa-plus-minus',
                    on_click=self.on_toggle_tool).tooltip(text)

                ui.separator()

                text = 'shift tile left'
                ui.button(icon='fa-solid fa-arrow-left', on_click=self.shift_left).props('color=black').tooltip(text)

                text = 'shift tile right'
                ui.button(icon='fa-solid fa-arrow-right', on_click=self.shift_right).props('color=black').tooltip(text)

                text = 'shift tile up'
                ui.button(icon='fa-solid fa-arrow-up', on_click=self.shift_up).props('color=black').tooltip(text)

                text = 'shift tile down'
                ui.button(icon='fa-solid fa-arrow-down', on_click=self.shift_down).props('color=black').tooltip(text)

                text = 'mirror horizontally (non destructable)'
                ui.button(icon='fa-solid fa-arrows-left-right', on_click=self.mirror_tile_horizontally).props('color=black').tooltip(text)

                text = 'mirror vertically (non destructable)'
                ui.button(icon='fa-solid fa-arrows-up-down', on_click=self.mirror_tile_vertically).props('color=black').tooltip(text)

                ui.separator()

                ui.button(icon='fa-solid fa-copy', on_click=self.copy_to_clipboard).props('color=green').tooltip('copy pattern to clipboard')
                ui.button(icon='fa-solid fa-trash', on_click=self.clear).props('color=red').tooltip('erase tile completely')


    def build_grid(self) -> None:
        with ui.column().classes('gap-1'):
            with ui.row().classes('gap-1'):

                with ui.column().classes('gap-0'):
                    ui.label('Grid').classes('text-lg font-semibold')
                    for y in range(TILE_SIZE):
                        row_refs = []

                        with ui.row().classes('gap-0'):
                            for x in range(TILE_SIZE):
                                pixel = PixelElement(0, self.grid[y].get_combined())
                                pixel.on('mousedown', lambda e, px=x, py=y: self.click_on_grid(e, px, py))
                                pixel.on('mouseover', lambda e, px=x, py=y: self.click_on_grid(e, px, py))
                                pixel.on('contextmenu.prevent', lambda: None)
                                row_refs.append(pixel)
                        self.pixel_refs.append(row_refs)


    def get_label(self, index):
        n = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
        return ['', 'F', 'B', 'FB'][n]


    def build_sidebar(self) -> None:
        with ui.column().classes('gap-4 min-w-[260px]'):
            header('Palette')

            with ui.row().classes('gap-2 flex-wrap max-w-[240px]'):
                for index, color in enumerate(PALETTE[1:], start=1):
                    sel = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
                    # chicungunha
                    button = ui.button(self.get_label(index)) \
                        .style(
                            f'''
                            width: 40px;
                            height: 40px;
                            background-color: {color};
                            border: 2px solid #444;
                            overflow: hidden;
                            '''
                        ) \
                        .tooltip(color) \
                        .props(f'{color=} text-color={get_text_color(color)}') \
                        .on('click', lambda e, i=index: self.select_fg_color(e, i)) \
                        .on('contextmenu.prevent', lambda e, i=index: self.select_bg_color(e, i))
                    if sel & 1: self.last_fg_button = button
                    if sel & 2: self.last_bg_button = button


    def toggle_confirm_erasing(self, e: events.ValueChangeEventArguments) -> None:
        self.confirm_erasing = e.value


    def toggle_background_occlusion(self, e: events.ValueChangeEventArguments) -> None:
        self.background_occlusion = e.value


    def select_tool(self, sender: ui.element) -> None:
        if self.last_tool_button:
            self.last_tool_button._props.pop('outline', None)
        sender.props('outline')
        self.last_tool_button = sender


    def on_toggle_tool(self, event) -> None:
        self.select_tool(event.sender)


    def select_fg_color(self, event, index: int) -> None:
        tmp = self.current_fg_color
        self.current_fg_color = index
        if self.last_fg_button:
            self.last_fg_button.set_text(self.get_label(tmp))
        event.sender.set_text(self.get_label(index))
        self.last_fg_button = event.sender


    def select_bg_color(self, event, index: int) -> None:
        tmp = self.current_bg_color
        self.current_bg_color = index
        if self.last_bg_button:
            self.last_bg_button.set_text(self.get_label(tmp))
        event.sender.set_text(self.get_label(index))
        self.last_bg_button = event.sender


    def repaint(self) -> None:
        for y in range(TILE_SIZE):
            for x in range(TILE_SIZE):
                self.pixel_refs[y][x].repaint()


    def unpaint(self, x: int, y: int) -> None:
        self.grid.unset_pattern(x, y)
        self.pixel_refs[y][x].set_value(0)
        self.pixel_refs[y][x].repaint()


    def paint(self, x: int, y: int) -> None:
        self.grid.set_pattern(x, y)
        self.pixel_refs[y][x].set_value(1)
        self.pixel_refs[y][x].repaint()


    def paint_fg(self, index: int, x: int, y: int) -> None:
        self.grid.set_fg(y, index)
        # repaint fg color if it changed
        for x in range(TILE_SIZE):
            self.pixel_refs[y][x].set_colors(None, self.grid[y].get_fg())


    def paint_bg(self, index: int, x: int, y: int) -> None:
        self.grid.set_bg(y, index)
        # update bg color if it changed
        for x in range(TILE_SIZE):
            self.pixel_refs[y][x].set_colors(None, None, self.grid[y].get_bg())


    def drag_combinedbrush(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint(x, y)
            self.paint_fg(self.current_fg_color, x, y)
        elif buttons == 2:
            self.paint_bg(self.current_bg_color, x, y)


    def drag_patternbrush(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint(x, y)
        elif buttons == 2:
            self.unpaint(x, y)


    def drag_colorbrush(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint_fg(self.current_fg_color, x, y)
        elif buttons == 2:
            self.paint_bg(self.current_bg_color, x, y)


    async def click_on_grid(self, event, x: int, y:int) -> None:
        # discard mouseover when no button is pressed
        buttons = event.args.get('buttons', 0)
        if buttons == 0: return
        self.dirty = True
        if self.last_tool_button is self.combinedbrush:
            return self.drag_combinedbrush(buttons, x, y)
        if self.last_tool_button is self.patternbrush:
            return self.drag_patternbrush(buttons, x, y)
        if self.last_tool_button is self.colorbrush:
            return self.drag_colorbrush(buttons, x, y)
        if self.last_tool_button is self.eraser:
            return self.unpaint(x, y)
        if self.last_tool_button is self.inverter:
            return self.invert_line(y)
        await show_message_dialog('Not implemented yet.')


    def click_on_grid_old(self, event: int, x: int, y: int) -> None:
        # discard mouseover when no button is pressed
        buttons = event.args.get('buttons', 0)
        if buttons == 0: return
        if buttons == 1:
            if self.grid.get_fg(y) == self.current_fg_color: return
            self.grid.set_fg(y, self.current_fg_color)
        if buttons == 2:
            if self.grid.get_bg(y) == self.current_bg_color: return
            self.grid.set_bg(y, self.current_bg_color)
        self.dirty = True
        self.repaint()


    def invert_line(self, y: int) -> None:
        fg, bg = self.grid.get_fg(y), self.grid.get_bg(y)
        self.grid[y].set_fg(bg)
        self.grid[y].set_bg(fg)
        self.grid[y].pattern = 0xff & ~self.grid[y].pattern
        self.repaint()


    async def clear(self) -> None:
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


    def on_set_copy_format(self, event: events.ValueChangeEventArguments) -> None:
        self.grid.set_copy_format(event.value)


    def copy_to_clipboard(self, event: events.ClickEventArguments) -> None:
        self.grid.set_copy_style(self.bla)
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
