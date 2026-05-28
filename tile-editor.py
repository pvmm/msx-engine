from nicegui import ui
from typing import List, Tuple

TILE_SIZE = 8           # 8 or 16
PIXEL_SCALE = 24        # visual size of each pixel
PALETTE = [
    '#000000', '#ffffff', '#ff0000', '#00ff00',
    '#0000ff', '#ffff00', '#ff00ff', '#00ffff',
    '#808080', '#ffa500', '#800080', '#8b4513',
]


class TileEditor:
    def __init__(self, size: int = TILE_SIZE):
        self.size = size
        self.current_fg_color_label = None
        self.current_fg_color = PALETTE[1]
        self.current_bg_color_label = None
        self.current_bg_color = PALETTE[0]
        self.last_fg_button = None
        self.last_bg_button = None
        self.grid: List[List[str]] = [
            ['#ffffff' for _ in range(size)]
            for _ in range(size)
        ]

        self.pixel_refs: List[List[ui.element]] = []

        self.build_ui()

    def build_ui(self) -> None:
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
                                    background-color: {self.grid[y][x]};
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

    def build_sidebar(self) -> None:
        with ui.column().classes('gap-4 min-w-[260px]'):
            ui.label('Palette').classes('text-lg font-semibold')

            with ui.row().classes('gap-2 flex-wrap max-w-[240px]'):
                for index, color in enumerate(PALETTE):
                    ui.button('') \
                        .style(
                            f'''
                            width: 40px;
                            height: 40px;
                            background-color: {color};
                            border: 2px solid #444;
                            '''
                        ) \
                        .props(f'{color=}') \
                        .on('click', lambda e, i=index, c=color: self.select_fg_color(e, i, c)) \
                        .on('contextmenu.prevent', lambda e, i=index, c=color: self.select_bg_color(e, i, c))

            self.current_fg_color_label = ui.label(
                f'Current foreground color: {self.current_fg_color} (1)'
            ).classes('font-mono').style('color: red;')
            self.current_bg_color_label = ui.label(
                f'Current background color: {self.current_bg_color} (0)'
            ).classes('font-mono').style('color: blue;')

            ui.separator()

            ui.label('Tools').classes('text-lg font-semibold')

            with ui.row().classes('gap-2'):
                ui.button('Clear', on_click=self.clear)
                ui.button('Fill', on_click=self.fill)

            ui.separator()

            ui.label('Export').classes('text-lg font-semibold')

            self.output = ui.textarea(
                label='Tile Data',
                value='',
            ).props('readonly').classes('w-full')

            with ui.row().classes('gap-2'):
                ui.button('Export Hex', on_click=self.export_hex)
                ui.button('Export RGB', on_click=self.export_rgb)

    def select_fg_color(self, event, index, color: str) -> None:
        if self.last_fg_button:
            self.last_fg_button.style('border: 2px solid #444;')
        event.sender.style('border: 4px solid red;')
        self.current_fg_color = color
        self.current_fg_color_label.set_text(
            f'Current foreground color: {color} ({index})'
        ).style('color: red;')
        self.last_fg_button = event.sender

    def select_bg_color(self, event, index, color: str) -> None:
        if self.last_bg_button:
            self.last_bg_button.style('border: 2px solid #444;')
        event.sender.style('border: 4px solid blue;')
        self.current_bg_color = color
        self.current_bg_color_label.set_text(
            f'Current background color: {color} ({index})'
        ).style('color: blue;')
        self.last_bg_button = event.sender

    def paint(self, color, x: int, y: int) -> None:
        self.grid[y][x] = color
        self.pixel_refs[y][x].style(
            f'''
            width: {PIXEL_SCALE}px;
            height: {PIXEL_SCALE}px;
            background-color: {color};
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

            for color in row:
                rgb_row.append(str(self.hex_to_rgb(color)))

            lines.append(', '.join(rgb_row))

        self.output.value = '\n'.join(lines)

    @staticmethod
    def hex_to_rgb(color: str) -> Tuple[int, int, int]:
        color = color.lstrip('#')

        return (
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16),
        )


TileEditor()

ui.run(
    title='NiceGUI Tile Editor',
    reload=False,
)

