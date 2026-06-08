from nicegui import ui
from typing import List, Tuple

from common import header, get_text_color, menu_item
from v9918 import Row8x8, Tile8x8, TILE_SIZE, FIRST_FG_COLOR, FIRST_BG_COLOR, PALETTE
import v9918

# constants
GRID_PIXEL_SIZE = 32        # size of each grid pixel
GRID_FG_LAYER_SIZE = 16        # size of foreground color pixel

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


class TileEditor:
    current_fg_color = FIRST_FG_COLOR
    current_bg_color = FIRST_BG_COLOR
    last_fg_button = None
    last_bg_button = None
    last_tool_button = None
    last_selected_tool = None
    # display dialog when erasing?
    confirm_erasing = True
    # data has changed and need saving?
    dirty = False

    def __init__(self, parent: ui.element, title: str = None):
        self.title = title
        self.parent = parent

        # UI elements to remember
        self.grid = Tile8x8(self.current_fg_color, self.current_bg_color)
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
                            ui.switch(menu_item('Confirm before erasing'), value=self.confirm_erasing,
                                      on_change=lambda e: self.toggle_confirm_erasing(e))
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
                text = 'paintbrush\nleft click: draw pixel\nright click: erase pixel'
                self.paintbrush = ui.button(icon='fa-solid fa-paintbrush',
                    on_click=lambda e: self.on_toggle_tool(e, 'paintbrush')).tooltip(text).props('outline')
                self.last_tool_button = self.paintbrush

                self.eraser = ui.button(icon='fa-solid fa-eraser',
                    on_click=lambda e: self.on_toggle_tool(e, 'eraser')).tooltip('eraser')
                self.eraser.visible = not TOGGLE_MODE

                text = 'inverter\nswitch foreground and background colors and invert pattern in a single line (non destructable)'
                ui.button(icon='fa-solid fa-plus-minus',
                    on_click=lambda e: self.on_toggle_tool(e, 'inverter')).tooltip(text)

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
                                pixel = ui.card().tight().on(
                                    'mousedown', lambda e, px=x, py=y: self.click_on_grid(e, px, py)
                                ).on(
                                    'mouseover', lambda e, px=x, py=y: self.click_on_grid(e, px, py)
                                ).on(
                                    'contextmenu.prevent', lambda: None
                                )

                                self.set_grid_pixel_style(pixel, self.grid[y][x])
                                row_refs.append(pixel)

                        self.pixel_refs.append(row_refs)

                with ui.column().classes('gap-0'):
                    ui.label('B[F]').tooltip('outside: background color\ninside: foreground color').style('width: 100%; text-align: center').classes('center text-lg font-semibold')
                    for y in range(TILE_SIZE):
                        with ui.row().classes('gap-0'):
                            with ui.card().tight().style('display: flex; justify-content: center; align-items: center;') as bg:
                                bg.on('mousedown', lambda e, px=x, py=y: self.click_on_color(e, px, py))
                                bg.on('mouseover', lambda e, px=x, py=y: self.click_on_color(e, px, py))
                                bg.on('contextmenu.prevent', lambda: None)
                                fg = ui.card().tight().classes('items-center justify-center')
                                self.set_grid_fg_style(fg, self.grid.get_fg(y))

                                self.fg_color_refs.append(fg)
                                self.bg_color_refs.append(bg)

                            self.set_grid_pixel_style(bg, self.grid.get_bg(y))

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

            ui.separator()

            header('Export')

            self.output = ui.textarea(
                label='Tile Data',
                value='',
            ).props('readonly').classes('w-full')

            with ui.row().classes('gap-2'):
                ui.button('Export Hex', on_click=self.export_hex)
                ui.button('Export RGB', on_click=self.export_rgb)

    def toggle_confirm_erasing(self, e) -> None:
        self.confirm_erasing = e.value

    def select_tool(self, sender, tool: str) -> None:
        if self.last_tool_button:
            self.last_tool_button._props.pop('outline', None)
        sender.props('outline')
        self.last_selected_tool = tool
        self.last_tool_button = sender

    def on_toggle_tool(self, event, tool: str) -> None:
        self.select_tool(event.sender, tool)

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

    def set_grid_fg_style(self, element, fg: int) -> None:
        element.style(
            f'''
            width: {GRID_FG_LAYER_SIZE}px;
            height: {GRID_FG_LAYER_SIZE}px;
            background-color: {PALETTE[fg]};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )

    def set_grid_pixel_style(self, element, combined: int) -> None:
        fg, bg = v9918.divide_colors(combined)
        element.style(
            f'''
            width: {GRID_PIXEL_SIZE}px;
            height: {GRID_PIXEL_SIZE}px;
            background-color: {PALETTE[fg or bg]};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )

    def repaint(self) -> None:
        for y in range(0, TILE_SIZE):
            for x in range(0, TILE_SIZE):
                self.set_grid_pixel_style(self.pixel_refs[y][x], self.grid[y][x])
            # repaint color column
            self.set_grid_fg_style(self.fg_color_refs[y], self.grid.get_fg(y))
            self.set_grid_pixel_style(self.bg_color_refs[y], self.grid.get_bg(y))

    def unpaint(self, x: int, y: int) -> None:
        self.grid.unset_pattern(x, y)
        self.set_grid_pixel_style(self.pixel_refs[y][x], self.grid[y][x])

    def paint(self, x: int, y: int) -> None:
        if not self.eraser.visible:
            global toggle_mode_status
            if toggle_mode_status == OFF:
                toggle_mode_status = int(v9918.select_fg(self.grid[y][x]) == self.current_fg_color)
                if toggle_mode_status:
                    self.set_pixel_function = self.grid.unset_pattern
                else:
                    self.set_pixel_function = self.grid.set_pattern

        self.set_pixel_function(x, y)
        self.set_grid_pixel_style(self.pixel_refs[y][x], self.grid[y][x])

    def paint_bg(self, index: int, x: int, y: int) -> None:
        self.grid.set_bg(y, index)
        # update background colour
        for x in range(0, TILE_SIZE):
            pixel = self.grid[y][x]
            self.set_grid_pixel_style(self.pixel_refs[y][x], pixel)

    def drag_paint(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint(x, y)
        elif buttons == 2:
            self.unpaint(x, y)

    async def click_on_grid(self, event, x: int, y:int) -> None:
        # discard mouseover when no button is pressed
        buttons = event.args.get('buttons', 0)
        if buttons == 0:
            global toggle_mode_status
            toggle_mode_status = OFF
            return
        self.dirty = True
        if self.last_selected_tool == 'paintbrush':
            return self.drag_paint(buttons, x, y)
        if self.last_selected_tool == 'eraser':
            return self.unpaint(x, y)
        if self.last_selected_tool == 'inverter':
            return self.invert_line(y)
        await show_message_dialog('Not implemented yet.')

    def click_on_color(self, event: int, x: int, y: int) -> None:
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

    def export_hex(self) -> None:
        lines = []

        for row in self.grid:
            lines.append(', '.join(row))

        self.output.value = '\n'.join(lines)

    def export_rgb(self) -> None:
        lines = []

        for row in self.grid:
            rgb_row = []

            for index in row:
                rgb_row.append(str(hex_to_rgb(PALETTE[index])))

            lines.append(', '.join(rgb_row))

        self.output.value = '\n'.join(lines)


if __name__ in {"__main__", "__mp_main__"}:
    from common import run
    with ui.row():
        TileEditor(ui.column().classes('w-full'))
    run()
