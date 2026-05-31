from nicegui import ui
from typing import List, Tuple

import colors

FIRST_BG_COLOR = 1
FIRST_FG_COLOR = 15
TILE_SIZE = 8           # 8 or 16
PIXEL_SCALE = 24        # visual size of each pixel
PALETTE = [
    '#000000', '#000000', '#3eb849', '#74d07d',
    '#5955e0', '#8076f1', '#b95e51', '#65dbef',
    '#db6559', '#ff897d', '#ccc35e', '#ded087',
    '#3aa241', '#b766b5', '#cccccc', '#ffffff',
]

async def show_message_dialog(message):
    with ui.dialog() as dialog, ui.card():
        ui.label(message)
        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit('OK'))
    result = await dialog


class Row8x8:
    def __init__(self):
        self.pattern = 0
        # color encoding = (foreground color index << 4) | background color index
        self.colors = 0

    def set_fg(self, x, index):
        # toggle foreground pixel
        if index == (self.colors >> 4) & 0x0f:
            self.pattern ^= 1 << (7 - x)
        # replace foreground color
        self.colors = (self.colors & 0x0f) | ((index << 4) & 0xf0)

    def set_bg(self, _, index):
        # replace background color
        self.colors = (self.colors & 0xf0) | (index & 0x0f)

    def __getitem__(self, x):
        return self.colors if self.pattern & (1 << (7 - x)) else colors.select_bg(self.colors)


class Tile8x8:
    def __init__(self):
        self.patterns: List[Row8x8] = [Row8x8() for _ in range(TILE_SIZE)]

    def __getitem__(self, index):
        return self.patterns[index]

    def __setitem__(self, index, value):
        self.patterns[index] = value

    def set_fg(self, x, y, index):
        self.patterns[y].set_fg(x, index)

    def set_bg(self, x, y, index):
        self.patterns[y].set_bg(x, index)


class TileEditor:
    def __init__(self, parent):
        self.parent = parent
        self.current_fg_color = FIRST_FG_COLOR
        self.current_bg_color = FIRST_BG_COLOR
        self.last_fg_button = None
        self.last_bg_button = None
        self.last_tool_button = None
        self.current_tool = 'pb'
        self.grid = Tile8x8()
        self.pixel_refs: List[List[ui.element]] = []
        self.build_ui()

    def build_ui(self) -> None:
        with self.parent:
            ui.label(f'{TILE_SIZE}x{TILE_SIZE} Tile Editor').classes(
                'text-2xl font-bold'
            )

            with ui.row().classes('items-start gap-8'):
                self.build_canvas()
                self.build_sidebar()

    def build_canvas(self) -> None:
        with ui.column().classes('gap-1'):
            ui.label('Canvas').classes('text-lg font-semibold')

            with ui.column().classes('gap-0'):
                for y in range(TILE_SIZE):
                    row_refs = []

                    with ui.row().classes('gap-0'):
                        for x in range(TILE_SIZE):
                            pixel = ui.card().on(
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
                        .props(f'{color=} text-color={colors.get_text_color(color)}') \
                        .on('click', lambda e, i=index: self.select_fg_color(e, i)) \
                        .on('contextmenu.prevent', lambda e, i=index: self.select_bg_color(e, i))
                    if sel & 1: self.last_fg_button = button
                    if sel & 2: self.last_bg_button = button

            ui.separator()

            with ui.row().classes('gap-2'):
                # outline default tool
                self.last_tool_button = \
                        ui.button(icon='fa-solid fa-paintbrush', on_click=self.toggle_tool).tooltip('paintbrush').props('tool=pb outline')
                ui.button(icon='fa-solid fa-fill-drip', on_click=self.toggle_tool).tooltip('fill').props('tool=fl')
                ui.button(icon='fa-solid fa-trash', on_click=self.clear).tooltip('delete').props('color=red')

            ui.separator()

            ui.label('Export').classes('text-lg font-semibold')

            self.output = ui.textarea(
                label='Tile Data',
                value='',
            ).props('readonly').classes('w-full')

            with ui.row().classes('gap-2'):
                ui.button('Export Hex', on_click=self.export_hex)
                ui.button('Export RGB', on_click=self.export_rgb)

    def toggle_tool(self, event) -> None:
        if self.last_tool_button:
            self.last_tool_button._props.pop('outline', None)
        event.sender.props('outline')
        self.current_tool = event.sender._props.get('tool')
        self.last_tool_button = event.sender

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

    def set_pixel_style(self, element, combined) -> None:
        fg, bg = colors.divide(combined)
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

    def paint(self, index, x: int, y: int) -> None:
        self.grid.set_fg(x, y, index)
        self.set_pixel_style(self.pixel_refs[y][x], self.grid[y][x])
        # display foreground color clash
        for x in range(0, TILE_SIZE):
            pixel = self.grid[y][x]
            self.set_pixel_style(self.pixel_refs[y][x], pixel)

    def paint_bg(self, index, x: int, y: int) -> None:
        self.grid.set_bg(x, y, index)
        # display background color clash
        for x in range(0, TILE_SIZE):
            pixel = self.grid[y][x]
            self.set_pixel_style(self.pixel_refs[y][x], pixel)

    def drag_paint(self, event, x: int, y: int) -> None:
        buttons = event.args.get('buttons', 0)
        if buttons == 1:
            self.paint(self.current_fg_color, x, y)
        elif buttons == 2:
            self.paint_bg(self.current_bg_color, x, y)

    async def click_on_canvas(self, event, x: int, y:int) -> None:
        # discard mouseover when no button is pressed
        buttons = event.args.get('buttons', 0)
        if buttons == 0: return
        tool = self.last_tool_button._props.get('tool')
        if tool == 'pb':
            self.drag_paint(event, x, y)
        else:
            await show_message_dialog('Not implemented yet.')

    def clear(self) -> None:
        for y in range(TILE_SIZE):
            for x in range(TILE_SIZE):
                self.paint(self.current_bg_color, x, y)

    def fill(self) -> None:
        for y in range(TILE_SIZE):
            for x in range(TILE_SIZE):
                self.paint(self.current_fg_color, x, y)

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
                rgb_row.append(str(colors.hex_to_rgb(PALETTE[index])))

            lines.append(', '.join(rgb_row))

        self.output.value = '\n'.join(lines)


if __name__ == '__main__':
    ui.add_head_html('<script src="https://kit.fontawesome.com/e374aa0b36.js" crossorigin="anonymous"></script>')
    with ui.row():
        TileEditor(ui.column())
    ui.run(
        title='NiceGUI Tile Editor',
        reload=False,
    )
