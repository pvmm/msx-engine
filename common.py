# functions
from nicegui import ui

def run() -> None:
    # Inject your personal Font Awesome Kit script into the document head
    ui.add_head_html('<script src="https://kit.fontawesome.com/dd0877df2c.js" crossorigin="anonymous"></script>')

    # Change tooltip size
    ui.add_css('.q-tooltip { font-size: 18px; white-space: pre-line; }')

    ui.run(title='NiceGUI Tile Editor') 
    

def header(text: str) -> ui.element:
    'Common header format'
    with ui.element('div'):
        return ui.label(text).classes('text-2xl font-semibold')


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
    r, g, b = hex_to_rgb(bg_color)
    luma: float = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    return 'black' if luma > 0.5 else 'white'


def menu_item(element: ui.element) -> ui.element:
    'Mickeymouses weird spacing issue of the menu item'
    return element.classes('mx-4')