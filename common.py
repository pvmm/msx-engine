# functions
from nicegui import ui

def header(text):
    ui.element('div')
    return ui.label(text).classes('text-lg font-semibold')

def hex_to_rgb(hex_string: str) -> [int, int, int]:
    hex_string = hex_string.lstrip('#')
    if len(hex_string) != 6:
        raise ValueError("Hex string must contain 6 hexadecimal digits")
    r = int(hex_string[0:2], 16)
    g = int(hex_string[2:4], 16)
    b = int(hex_string[4:6], 16)
    return (r, g, b)

def get_text_color(bg_color: str) -> str:
    'Define text color to be distinct of background color'
    r, g, b = hex_to_rgb(bg_color)
    luma = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    color = 'black' if luma > 0.5 else 'white'
    return color

def menu_item(text):
    return text + '\u00A0\u00A0\u00A0\u00A0'
