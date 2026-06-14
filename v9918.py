# V9918 tile mode

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


def mirror(pattern: int) -> int:
    pattern = ((pattern & 0xF0) >> 4) | ((pattern & 0x0F) << 4)
    pattern = ((pattern & 0xCC) >> 2) | ((pattern & 0x33) << 2)
    pattern = ((pattern & 0xAA) >> 1) | ((pattern & 0x55) << 1)
    return pattern


def grid_to_svg(grid: list[list[int]], scale: int = 20) -> str:
    width = len(grid[0])
    height = len(grid)

    svg = [ f'''<svg xmlns="http://www.w3.org/2000/svg"
            width="{width * scale}"
            height="{height * scale}">''' ]
    for y in range(height):
        for x in range(width):
            fg = select_fg(grid[y][x])
            bg = select_bg(grid[y][x])
            svg.append(
                f'<rect '
                f'x="{x * scale}" '
                f'y="{y * scale}" '
                f'width="{scale}" '
                f'height="{scale}" '
                f'fill="{PALETTE[fg or bg]}" '
                f'stroke="#444"/>'
            )
    svg.append('</svg>')
    return ''.join(svg)


# classes
class Row8:
    def __init__(self, fg: int = 0, bg: int = 0):
        # toggle mode: activate an active pixel again to deactivate it
        self.pattern = 0
        # color encoding = (foreground color index << 4) | background color index
        self.colors = combine_colors(fg, bg)


    def __str__(self) -> str:
        return f'Row({bin(self.pattern)},{hex(self.colors)})'


    def __len__(self) -> int:
        return 8


    def copy(self, row8: Row8) -> None:
        self.pattern = row8.pattern
        self.colors = row8.colors


    def set_fg(self, index: int) -> None:
        # replace foreground color (the infamous color clash)
        self.colors = (self.colors & 0x0f) | ((index << 4) & 0xf0)


    def get_pixel(self, x: int) -> int:
        return not not self.pattern & (1 << (7 - x))


    def set_pattern(self, x: int) -> None:
        self.pattern |= 1 << (7 - x)


    def unset_pattern(self, x: int) -> None:
        self.pattern &= ~(1 << (7 - x))


    def set_bg(self, index: int) -> None:
        # replace background color
        self.colors = (self.colors & 0xf0) | (index & 0x0f)


    def get_fg(self) -> int:
        return select_fg(self.colors)


    def get_bg(self) -> int:
        return select_bg(self.colors)


    def get_combined(self) -> int:
        return self.colors


    def __getitem__(self, x: int) -> int:
        return self.colors if self.pattern & (1 << (7 - x)) else select_bg(self.colors)


    def mirror(self) -> None:
        '''mirror pattern inplace'''
        self.pattern = mirror(self.pattern)


    def shift_left(self) -> None:
        self.pattern = ((self.pattern << 1) | (self.pattern >> 7)) & 0xFF


    def shift_right(self) -> None:
        self.pattern = ((self.pattern >> 1) | (self.pattern << 7)) & 0xFF


class Tile8x8:
    def __init__(self, fg: int = 0, bg: int = 0):
        self.patterns: list[Row8] = [Row8(fg, bg) for _ in range(TILE_SIZE)]


    def __str__(self) -> str:
        return f'Tile8x8({' '.join([str(x) for x in self.patterns])})'


    def __len__(self) -> int:
        return 8


    def __getitem__(self, index: int) -> Row8:
        return self.patterns[index]


    def __setitem__(self, index: int, value: Row8) -> None:
        self.patterns[index] = value


    @staticmethod
    def copy(tile8x8: Tile8x8) -> Tile8x8:
        self = Tile8x8()
        for i, row in enumerate(tile8x8.patterns):
            self.patterns[i].copy(row)
        return self


    def get_pixel(self, x: int, y: int) -> int:
        return self.patterns[y].get_pixel(x)


    def set_pattern(self, x: int, y: int) -> None:
        self.patterns[y].set_pattern(x)


    def unset_pattern(self, x: int, y: int) -> None:
        self.patterns[y].unset_pattern(x)


    def set_fg(self, y: int, index: int) -> None:
        self.patterns[y].set_fg(index)


    def set_bg(self, y: int, index: int) -> None:
        self.patterns[y].set_bg(index)


    def get_fg(self, y: int) -> int:
        return self.patterns[y].get_fg()


    def get_bg(self, y: int) -> int:
        return self.patterns[y].get_bg()


    def get_combined(self, y: int) -> int:
        return self.patterns[y].get_combined()


    def mirror_horizontally(self) -> None:
        '''mirror horizontally inplace'''
        for y in range(TILE_SIZE):
            self.patterns[y].mirror()


    def mirror_vertically(self) -> None:
        tmp: list[Row8] = [Row8() for _ in range(TILE_SIZE)]
        for y in range(TILE_SIZE):
            tmp[TILE_SIZE - y - 1] = self.patterns[y]
        self.patterns = tmp


    def shift_left(self) -> None:
        '''shift horizontally inplace'''
        for y in range(TILE_SIZE):
            self.patterns[y].shift_left()


    def shift_right(self) -> None:
        '''shift horizontally inplace'''
        for y in range(TILE_SIZE):
            self.patterns[y].shift_right()


    def shift_up(self) -> None:
        tmp: list[Row8] = [Row8() for _ in range(TILE_SIZE)]
        for y in range(TILE_SIZE):
            tmp[(y - 1) % TILE_SIZE] = self.patterns[y]
        self.patterns = tmp


    def shift_down(self) -> None:
        tmp: list[Row8] = [Row8() for _ in range(TILE_SIZE)]
        for y in range(TILE_SIZE):
            tmp[(y + 1) % TILE_SIZE] = self.patterns[y]
        self.patterns = tmp


    def set_copy_format(self, format: str) -> None:
        pass

