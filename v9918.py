# constants
FIRST_BG_COLOR = 1
FIRST_FG_COLOR = 15
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

def divide_colors(combined: int) -> [int, int]:
    return select_fg(combined), select_bg(combined)

def combine_colors(fg_color: int, bg_color: int) -> int:
    "Set background and foreground pixel colors"
    return ((fg_color << 4) & 0xf0) | (bg_color & 0x0f)

# classes
class Row8x8:
    def __init__(self):
        # toggle mode: activate an active pixel again to deactivate it
        self.pattern = 0
        # color encoding = (foreground color index << 4) | background color index
        self.colors = 0

    def set_fg(self, x, index):
        self.pattern |= 1 << (7 - x)
        # replace foreground color (the infamous color clash)
        self.colors = (self.colors & 0x0f) | ((index << 4) & 0xf0)

    def unset_fg(self, x):
        self.pattern &= ~(1 << (7 - x))

    def set_bg(self, _, index):
        # replace background color
        self.colors = (self.colors & 0xf0) | (index & 0x0f)

    def __getitem__(self, x):
        return self.colors if self.pattern & (1 << (7 - x)) else select_bg(self.colors)


class Tile8x8:
    def __init__(self):
        self.patterns: List[Row8x8] = [Row8x8() for _ in range(TILE_SIZE)]

    def __getitem__(self, index):
        return self.patterns[index]

    def __setitem__(self, index, value):
        self.patterns[index] = value

    def set_fg(self, x, y, index):
        self.patterns[y].set_fg(x, index)

    def unset_fg(self, x, y, index = 0):
        self.patterns[y].unset_fg(x)

    def set_bg(self, x, y, index):
        self.patterns[y].set_bg(x, index)


