from nicegui import ui
from typing import List, Tuple

import colors

FIRST_BG_COLOR = 0
FIRST_FG_COLOR = 14
TILE_SIZE = 8           # 8 or 16
PIXEL_SCALE = 24        # visual size of each pixel
PALETTE = [
    '#000000', '#3eb849', '#74d07d',
    '#5955e0', '#8076f1', '#b95e51', '#65dbef',
    '#db6559', '#ff897d', '#ccc35e', '#ded087',
    '#3aa241', '#b766b5', '#cccccc', '#ffffff',
]


class TileEditor:
    def __init__(self, parent, size: int = TILE_SIZE):
        self.parent = parent
        self.size = size
        self.current_fg_color = FIRST_FG_COLOR
        self.current_bg_color = FIRST_BG_COLOR
        self.last_fg_button = None
        self.last_bg_button = None
        self.last_tool_button = None
        self.current_tool = 'pb'
        self.grid: List[List[str]] = [
            [self.current_bg_color for _ in range(size)]
            for _ in range(size)
        ]

        self.pixel_refs: List[List[ui.element]] = []

        self.build_ui()

    def build_ui(self) -> None:
        with self.parent:
            #ui.add_head_html('<link rel="stylesheet" href="https://cloudflare.com">')
            #ui.add_head_html('<link href="https://cdn.jsdelivr.net/themify-icons/0.1.2/css/themify-icons.css" rel="stylesheet" />')

            ui.label(f'{self.size}x{self.size} Tile Editor').classes(
                'text-2xl font-bold'
            )

            with ui.row().classes('items-start gap-8'):
                self.build_canvas()
                self.build_sidebar()

    def build_canvas(self) -> None:
        with ui.column().classes('gap-1'):
            ui.label('Canvas').classes('text-lg font-semibold')

            with ui.column().classes('gap-0'):
                for y in range(self.size):
                    row_refs = []

                    with ui.row().classes('gap-0'):
                        for x in range(self.size):
                            pixel = (
                                ui.card()
                                .style(
                                    f'''
                                    width: {PIXEL_SCALE}px;
                                    height: {PIXEL_SCALE}px;
                                    background-color: {PALETTE[self.grid[y][x]]};
                                    border: 1px solid #444;
                                    border-radius: 0;
                                    cursor: pointer;
                                    '''
                                )
                            )
                            pixel.on(
                                'mousedown',
                                lambda e, px=x, py=y: self.drag_paint(e, px, py)
                            )
                            pixel.on(
                                'mouseover',
                                lambda e, px=x, py=y: self.drag_paint(e, px, py)
                            )
                            pixel.on('contextmenu.prevent', lambda: None)

                            row_refs.append(pixel)

                    self.pixel_refs.append(row_refs)

    def get_label(self, index):
        n = ((index == self.current_fg_color) << 0) | ((index == self.current_bg_color) << 1)
        return ['', 'F', 'B', 'FB'][n]

    def build_sidebar(self) -> None:
        with ui.column().classes('gap-4 min-w-[260px]'):
            ui.label('Palette').classes('text-lg font-semibold')

            with ui.row().classes('gap-2 flex-wrap max-w-[240px]'):
                for index, color in enumerate(PALETTE):
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

    def paint(self, index, x: int, y: int) -> None:
        self.grid[y][x] = index
        self.pixel_refs[y][x].style(
            f'''
            width: {PIXEL_SCALE}px;
            height: {PIXEL_SCALE}px;
            background-color: {PALETTE[index]};
            border: 1px solid #444;
            border-radius: 0;
            cursor: pointer;
            '''
        )

    def drag_paint(self, event, x: int, y: int) -> None:
        buttons = event.args.get('buttons', 0)
        if buttons:
            self.paint(self.current_fg_color if buttons == 1 else self.current_bg_color, x, y)

    def clear(self) -> None:
        for y in range(self.size):
            for x in range(self.size):
                self.paint(self.current_bg_color, x, y)

    def fill(self) -> None:
        for y in range(self.size):
            for x in range(self.size):
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
        TileEditor(ui.column(), 8)
    ui.run(
        title='NiceGUI Tile Editor',
        reload=False,
    )
