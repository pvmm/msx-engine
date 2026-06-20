# functions
import os
import json
import urllib

from typing import Any
from nicegui import ui, events, app
from nicegui.elements.mixins.disableable_element import DisableableElement
from nicegui.elements.interactive_image import InteractiveImage


# app-wide globals
SCREEN_WIDTH: int = 0
SCREEN_HEIGHT: int = 0


def screen_resize(e: events.GenericEventArguments) -> None:
    global SCREEN_WIDTH
    global SCREEN_HEIGHT
    SCREEN_WIDTH = e.args['width']
    SCREEN_HEIGHT = e.args['height']


def run() -> None:
    # Add static directory
    app.add_static_files('/static', os.path.join(os.path.dirname(__file__), 'static'))

    # Inject your personal Font Awesome Kit script into the document head
    ui.add_head_html('<link rel="stylesheet" href="static/css/all.min.css">', shared=True)

    # Get window size
    ui.add_head_html('''
        <script>
        function emitSize() {
            emitEvent('resize', {
                width: document.body.offsetWidth,
                height: document.body.offsetHeight,
            });
        }
        window.onload = emitSize;
        window.onresize = emitSize;
        </script>
    ''')
    ui.on('resize', lambda e: screen_resize(e))

    # Change tooltip size
    ui.add_css('''
        .q-tooltip {
            font-size: 18px; white-space: pre-line;
        }
        .no-select {
            user-select: none;
        }
    ''')

    # Remove default scroll_area padding
    ui.add_css('''
        .nicegui-scroll-area .q-scrollarea__content {
            padding: 0;
            margin: 0;
            overflow-x: scroll !important;
            overflow-y: scroll !important;
            opacity: 1 !important;
        }
        .q-scrollarea__thumb {
            opacity: 1 !important;
            background: #aaa;
            outline: 2px solid #000;
            border-radius: 6px;
        }
        .q-scrollarea__bar {
            opacity: 1 !important;
            background: #444;
            border-radius: 6px;
        }
    ''')

    ui.run(title='NiceGUI Tile Editor') 
    

def header(text: str) -> ui.element:
    'Common header format'
    with ui.element('div'):
        return ui.label(text).classes('text-2xl font-semibold')


def header2(text: str) -> ui.element:
    'Common header format'
    return ui.label(text).classes('text-lg font-semibold')


def hex_to_rgb(hex_string: str) -> tuple[int, int, int]:
    'Converts HTML #rrggbb to RGB triplet'
    hex_string = hex_string.lstrip('#')
    if len(hex_string) != 6:
        raise ValueError("Hex string must contain 6 hexadecimal digits")
    r = int(hex_string[0:2], 16)
    g = int(hex_string[2:4], 16)
    b = int(hex_string[4:6], 16)
    return (r, g, b)


def get_text_color(bg_color: str) -> str:
    'Returns a text color that is distinct from background color'
    if bg_color == 'transparent': bg_color = "#686868"
    r, g, b = hex_to_rgb(bg_color)
    luma: float = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    return 'black' if luma > 0.5 else 'white'


def menu_item(element: ui.element) -> ui.element:
    'Mickeymouses weird spacing issue of the menu item'
    return element.classes('mx-4')


def enable(element: DisableableElement | ui.element, status: bool = True) -> ui.element:
    """Enable/disable an element for any type of ui.element"""
    if isinstance(element, DisableableElement):
        if status:
            element.enable()
        else:
            element.disable()
    else:
        for slot in element.slots:
            for child in element.default_slot.children:
                enable(child, status)
        if status:
            element._props.pop('disabled')
        else:
            element.props('disabled')
    return element


def grid_to_svg(grid: TileNxN | list[list[int]], palette: list[str], scale: int = 20) -> str:
    width = len(grid[0])
    height = len(grid)

    svg = [ f'''<svg xmlns="http://www.w3.org/2000/svg"
            width="{width * scale}"
            height="{height * scale}">''' ]
    for y in range(height):
        for x in range(width):
            svg.append(
                f'<rect '
                f'x="{x * scale}" '
                f'y="{y * scale}" '
                f'width="{scale}" '
                f'height="{scale}" '
                f'fill="{palette[grid[y][x]]}" '
                f'stroke="#444"/>'
            )
    svg.append('</svg>')
    return ''.join(svg)


class UiMetatile(InteractiveImage):
    """Represents a metatile in the UI, allowing to display and select/unselect it."""
    grid: Any
    scale: int
    palette: list[str]

    def __init__(self, data: object | str | bytes | list[list[int]], palette: list[str], scale: int = 5):
        grid: Any
        super().__init__()
        self.palette = palette
        self.scale = scale
        if isinstance(data, list):
            grid = data
        elif isinstance(data, str) or isinstance(data, bytes):
            # Convert from json string
            grid = json.loads(data)
        else:
            grid = data
        self.reload(grid)


    def reload(self, grid: object | str | bytes | list[list[int]]) -> None:
        self.grid = grid
        data = grid_to_svg(grid, self.palette, self.scale)
        self.ui = self.set_source('data:image/svg+xml;utf8,' + urllib.parse.quote(data))