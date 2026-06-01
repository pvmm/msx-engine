from nicegui import ui
from typing import List, Tuple

from v9918 import Row8x8, Tile8x8, TILE_SIZE, FIRST_FG_COLOR, FIRST_BG_COLOR, PALETTE
import v9918

# constants
PIXEL_SCALE = 32        # visual size of each pixel

# toggle mode: switches between paintbrush and eraser automatically by context
TOGGLE_MODE = False
DEACTIVATE, ACTIVATE, OFF = 0, 1, 2

# Common settings
toggle_mode_status = OFF


def menu_item(text):
    return text + '\u00A0\u00A0\u00A0\u00A0'


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


# functions
def hex_to_rgb(hex_string: str) -> [int, int, int]:
    hex_string = hex_string.lstrip('#')
    if len(hex_string) != 6:
        raise ValueError("Hex string must contain 6 hexadecimal digits")
    r = int(hex_string[0:2], 16)
    g = int(hex_string[2:4], 16)
    b = int(hex_string[4:6], 16)
    return (r, g, b)


def get_text_color(bg_color: str) -> str:
    r, g, b = hex_to_rgb(bg_color)
    luma = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    return 'black' if luma > 0.5 else 'white'


class EraserProxy:
    visible = not TOGGLE_MODE


class TileEditor:
    def __init__(self, parent):
        self.parent = parent
        self.dirty = False

        self.current_fg_color = FIRST_FG_COLOR
        self.current_bg_color = FIRST_BG_COLOR

        self.last_fg_button = None
        self.last_bg_button = None
        self.last_tool_button = None

        self.eraser = EraserProxy()
        self.confirm_erasing = True

        self.grid = Tile8x8()
        self.pixel_refs: List[List[ui.element]] = []
        self.set_pixel_function = self.grid.set_fg
        self.build_ui()

    def build_ui(self) -> None:
        with self.parent:
            with ui.row().classes('items-center flex-nowrap'):
                with ui.button(icon='menu'):
                    with ui.menu().props('auto-close'):
                        with ui.column():
                            ui.switch(menu_item('Toggle smart paintbrush mode'), value=not self.eraser.visible,
                                      on_change=lambda e: self.toggle_eraser_tool(e))
                            ui.switch(menu_item('Confirm before erasing'), value=self.confirm_erasing,
                                      on_change=lambda e: self.toggle_confirm_erasing(e))
                ui.label(f'{TILE_SIZE}x{TILE_SIZE} Tile Editor').classes(
                    'text-2xl font-bold'
                )

            with ui.row().classes('items-start gap-8'):
                self.build_tools()
                self.build_canvas()
                self.build_sidebar()

    def build_tools(self) -> None:
        with ui.column().classes('gap-1'):
            ui.label('Tools').classes('text-lg font-semibold')
            with ui.row().classes('gap-2 flex-wrap max-w-[203px]'):
                # outline default tool
                text = 'paintbrush\nleft click: foreground color\nright click: background color'
                self.paintbrush = ui.button(icon='fa-solid fa-paintbrush', on_click=self.toggle_tool).tooltip(text).props('tool=pb outline')
                self.last_tool_button = self.paintbrush

                self.eraser = ui.button(icon='fa-solid fa-eraser', on_click=self.toggle_tool).tooltip('eraser').props('tool=er')
                self.eraser.visible = not TOGGLE_MODE

                text = 'inverter\nswitch foreground and background color and invert pattern in a single line (non destructable)'
                ui.button(icon='fa-solid fa-plus-minus').tooltip(text)

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

                ui.button(icon='fa-solid fa-trash', on_click=self.clear).props('color=black').tooltip('erase tile completely')

    def build_canvas(self) -> None:
        with ui.column().classes('gap-1'):
            ui.label('Canvas').classes('text-lg font-semibold')

            with ui.column().classes('gap-0'):
                for y in range(TILE_SIZE):
                    row_refs = []

                    with ui.row().classes('gap-0'):
                        for x in range(TILE_SIZE):
                            pixel = ui.card().tight().on(
                                'mousedown', lambda e, px=x, py=y: self.click_on_canvas(e, px, py)
                            ).on(
                                'mouseover', lambda e, px=x, py=y: self.click_on_canvas(e, px, py)
                            ).on(
                                'contextmenu.prevent', lambda: None
                            )

                            self.set_pixel_style(pixel, self.grid[y][x])
                            row_refs.append(pixel)

                    self.pixel_refs.append(row_refs)

    def get_label(self, index):
        n = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
        return ['', 'F', 'B', 'FB'][n]

    def build_sidebar(self) -> None:
        with ui.column().classes('gap-4 min-w-[260px]'):
            ui.label('Palette').classes('text-lg font-semibold')

            with ui.row().classes('gap-2 flex-wrap max-w-[240px]'):
                for index, color in enumerate(PALETTE[1:], start=1):
                    sel = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
                    # chicungunha
                    button = ui.button(self.get_label(index)) \
                        .style(
                            f'''
                            width: 40px;
                            height: 40px;
                            color: black;
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

            ui.label('Export').classes('text-lg font-semibold')

            self.output = ui.textarea(
                label='Tile Data',
                value='',
            ).props('readonly').classes('w-full')

            with ui.row().classes('gap-2'):
                ui.button('Export Hex', on_click=self.export_hex)
                ui.button('Export RGB', on_click=self.export_rgb)

    def toggle_eraser_tool(self, e) -> None:
        self.eraser.visible = not e.value
        if self.last_tool_button == self.eraser:
            self.select_tool(self.paintbrush)

    def toggle_confirm_erasing(self, e) -> None:
        self.confirm_erasing = e.value

    def select_tool(self, sender) -> None:
        if self.last_tool_button:
            self.last_tool_button._props.pop('outline', None)
        sender.props('outline')
        self.last_tool_button = sender

    def toggle_tool(self, event) -> None:
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

    def set_pixel_style(self, element, combined: int) -> None:
        fg, bg = v9918.divide_colors(combined)
        element.style(
            f'''
            width: {PIXEL_SCALE}px;
            height: {PIXEL_SCALE}px;
            background-color: {PALETTE[fg or bg]};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )

    def repaint(self) -> None:
        for y in range(0, TILE_SIZE):
            for x in range(0, TILE_SIZE):
                self.set_pixel_style(self.pixel_refs[y][x], self.grid[y][x])

    def unpaint(self, x: int, y: int) -> None:
        self.grid.unset_fg(x, y)
        self.set_pixel_style(self.pixel_refs[y][x], self.grid[y][x])

    def paint(self, index: int, x: int, y: int) -> None:
        if not self.eraser.visible:
            global toggle_mode_status
            if toggle_mode_status == OFF:
                toggle_mode_status = int(v9918.select_fg(self.grid[y][x]) == self.current_fg_color)
                if toggle_mode_status:
                    self.set_pixel_function = self.grid.unset_fg
                else:
                    self.set_pixel_function = self.grid.set_fg

        self.set_pixel_function(x, y, index)
        # update the infamous colour clash
        for x in range(0, TILE_SIZE):
            pixel = self.grid[y][x]
            self.set_pixel_style(self.pixel_refs[y][x], pixel)

    def paint_bg(self, index: int, x: int, y: int) -> None:
        self.grid.set_bg(x, y, index)
        # update background colour
        for x in range(0, TILE_SIZE):
            pixel = self.grid[y][x]
            self.set_pixel_style(self.pixel_refs[y][x], pixel)

    def drag_paint(self, buttons: int, x: int, y: int) -> None:
        if buttons == 1:
            self.paint(self.current_fg_color, x, y)
        elif buttons == 2:
            self.paint_bg(self.current_bg_color, x, y)

    async def click_on_canvas(self, event, x: int, y:int) -> None:
        # discard mouseover when no button is pressed
        buttons = event.args.get('buttons', 0)
        if buttons == 0:
            global toggle_mode_status
            toggle_mode_status = OFF
            return
        self.dirty = True
        tool = self.last_tool_button._props.get('tool')
        if tool == 'pb':
            return self.drag_paint(buttons, x, y)
        if tool == 'er':
            return self.unpaint(x, y)
        await show_message_dialog('Not implemented yet.')

    async def clear(self) -> None:
        result = await show_confirm_dialog('Are you sure you want to delete the tile?') \
                if self.confirm_erasing and self.dirty else 'yes'
        if result == 'yes':
            for y in range(TILE_SIZE):
                for x in range(TILE_SIZE):
                    self.grid.unset_fg(x, y)
            self.repaint()

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


if __name__ == '__main__':
    ui.add_head_html('<script src="https://kit.fontawesome.com/e374aa0b36.js" crossorigin="anonymous"></script>')
    ui.add_css('.q-tooltip { font-size: 18px; white-space: pre-line; }')
    with ui.row():
        TileEditor(ui.column())
    ui.run(
        title='NiceGUI Tile Editor',
        reload=False,
    )
