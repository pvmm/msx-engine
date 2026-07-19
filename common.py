import os
import json
import base64
import webcolors

from io import BytesIO
from typing import Callable, TypeVar
from nicegui import ui, events, app
from nicegui.elements.mixins.disableable_element import DisableableElement

from datatypes import Tile


# Type info

P = TypeVar("P")

# app-wide globals
SCREEN_WIDTH: int = 0
SCREEN_HEIGHT: int = 0
resize_event_subscribers: dict[str, Callable[[], None]] = {}

def file_to_base64(buffer: BytesIO) -> str:
    #image = Image.open(BytesIO(image))
    #image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/png;base64,{encoded}'


def subscribe_to_resize_event(name: str, function: Callable[[], None]) -> None:
    print(f'subscribe_to_resize_event({function})')
    if not name in resize_event_subscribers:
        resize_event_subscribers.update({name: function})


def screen_resize(e: events.GenericEventArguments) -> None:
    global SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH = e.args['width']
    SCREEN_HEIGHT = e.args['height']
    for name, function in resize_event_subscribers.items():
        function()


def add_handlers() -> None:
    # Get noticed when window size change
    ui.on('resize', lambda e: screen_resize(e))


def run(title: str, *, host: str = '0.0.0.0', port: int = 8080, reload: bool = True) -> None:
    # Add static directory
    app.add_static_files('/static', os.path.join(os.path.dirname(__file__), 'static'))

    # Inject your personal Font Awesome Kit script into the document head
    ui.add_head_html('<link rel="stylesheet" href="static/css/all.min.css">', shared=True)

    # Change tooltip size
    ui.add_css('''
        .q-tooltip {
            font-size: 18px; white-space: pre-line;
        }
        .no-select {
            user-select: none;
        }
    ''', shared=True)

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
    ''', shared=True)

    ui.run(title=title, host=host, port=port, reload=reload)
    

def header(text: str) -> ui.element:
    'first header format'
    with ui.element('div'):
        return ui.label(text).classes('text-2xl font-semibold')


def header2(text: str) -> ui.element:
    'second header format'
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


def get_text_color(bg: str) -> str:
    'Returns white/black text color that best matches the specified background color'
    if bg == 'transparent': bg = "#686868"
    try:
        r, g, b = hex_to_rgb(webcolors.name_to_hex(bg))
    except ValueError:
        r, g, b = hex_to_rgb(bg)
    luma: float = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    return 'black' if luma > 0.5 else 'white'


def menu_item(element: ui.element) -> ui.element:
    'Mickeymouses weird spacing issue of the menu item'
    return element.classes('mx-4')


def disable(element: DisableableElement | ui.element | P) -> DisableableElement | ui.element | P:
    """Short cut to disable an element for any type of ui.element"""
    return enable(element, False)


def enable(element: DisableableElement | ui.element | P, status: bool = True) -> DisableableElement | ui.element | P:
    """Enable/disable an element for any type of ui.element"""
    if isinstance(element, DisableableElement):
        if status:
            element.enable()
        else:
            element.disable()
    elif isinstance(element, ui.element):
        for slot in element.slots:
            for child in element.default_slot.children:
                enable(child, status)
        if status:
            element._props.pop('disabled')
        else:
            element.props('disabled')
    else:
        raise TypeError(F'don\'t know how to enable/disable type {type(element)}')
    return element
