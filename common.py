# functions
from nicegui import ui

def header(text: str) -> ui.element:
    'Common header format'
    ui.element('div')
    return ui.label(text).classes('text-2xl font-semibold')

def hex_to_rgb(hex_string: str) -> [int, int, int]:
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
    r, g, b = hex_to_rgb(bg_color)
    luma = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    return 'black' if luma > 0.5 else 'white'

def menu_item(text: str) -> str:
    'Mickeymouses weird spacing issue of the menu item'
    return text + '\u00A0\u00A0\u00A0\u00A0'

def enable(element: ui.element, status: bool = True) -> None:
    if status:
        element._props.pop('disabled')
    else:
        element.props('disabled')
