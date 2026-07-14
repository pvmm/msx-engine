#
# V9918 tile mode (SCREEN 2)
#

# constants
DEFAULT_FG_COLOR = 15   # white
DEFAULT_BG_COLOR = 1    # black
TILE_SIZE = 8           # 8 or 16
PALETTE = [
    '#000000', '#000000', '#3eb849', '#74d07d',
    '#5955e0', '#8076f1', '#b95e51', '#65dbef',
    '#db6559', '#ff897d', '#ccc35e', '#ded087',
    '#3aa241', '#b766b5', '#cccccc', '#ffffff',
]

# functions
def select_fg(combined: int) -> int:
    return (combined >> 4) & 0x0f


def select_bg(combined: int) -> int:
    return combined & 0x0f


def divide_colors(combined: int) -> tuple[int, int]:
    return select_fg(combined), select_bg(combined)


def combine_colors(fg_color: int, bg_color: int) -> int:
    "Set background and foreground pixel colors"
    return ((fg_color << 4) & 0xf0) | (bg_color & 0x0f)

