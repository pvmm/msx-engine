# functions

from nicegui import ui
from nicegui.elements.mixins.disableable_element import DisableableElement


def run() -> None:
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
        ''')

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


def enable(element: DisableableElement | ui.element, status: bool = True) -> None:
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

