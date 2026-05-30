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

def select_fg(combined: int) -> int:
    return (combined >> 4) & 0x0f

def select_bg(combined: int) -> int:
    return combined & 0x0f

def divide(combined: int) -> [int, int]:
    return select_fg(combined), select_bg(combined)

def combine(fg_color: int, bg_color: int) -> int:
    "Set background and foreground pixel colors"
    return ((fg_color << 4) & 0xf0) | (bg_color & 0x0f)
