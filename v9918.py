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


def grid_to_svg(grid: TileNxN | list[list[int]], scale: int = 20) -> str:
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
class RowN:
    pattern: list[bool]
    fg: int
    bg: int

    def __init__(self, fg: int = 0, bg: int = 0, width: int = 8):
        if width % 8 != 0:
            raise ValueError("width must be a multiple of 8")
        self.pattern = [False] * width
        self.fg = fg
        self.bg = bg


    def __str__(self) -> str:
        bin = ''
        for value in self.pattern:
            bin += '1' if value else '0'
        return f'Row(p:{bin},c:{hex(self.fg)}:{hex(self.bg)})'


    def __len__(self) -> int:
        return len(self.pattern)


    def __getitem__(self, x: int) -> int:
        """Return the foreground color index if the pixel is active, otherwise return the background color index."""
        return self.fg if self.pattern[x] else self.bg


    def copy(self, row: RowN) -> None:
        self.pattern = list(row.pattern)
        self.fg, self.bg = row.fg, row.bg


    def set_fg(self, fg: int) -> None:
        self.fg = fg


    def get_pixel(self, x: int) -> bool:
        return self.pattern[x]


    def set_pattern(self, x: int) -> None:
        self.pattern[x] = True


    def unset_pattern(self, x: int) -> None:
        self.pattern[x] = False


    def set_bg(self, bg: int) -> None:
        self.bg = bg


    def get_fg(self) -> int:
        return self.fg


    def get_bg(self) -> int:
        return self.bg


    def get_colors(self) -> tuple[int, int]:
        return self.fg, self.bg


    def invert(self) -> None:
        '''Invert pattern inplace'''
        for x in range(len(self)):
            self.pattern[x] = not self.pattern[x]


    def mirror(self) -> None:
        '''mirror pattern inplace'''
        self.pattern = list(reversed(self.pattern))


    def shift_left(self) -> None:
        '''shift left inplace'''
        self.pattern.append(self.pattern.pop(0))


    def shift_right(self) -> None:
        '''shift right inplace'''
        self.pattern.insert(0, self.pattern.pop())


class TileNxN:
    rows: list[RowN]

    @staticmethod
    def copy(tile: TileNxN) -> TileNxN:
        self = TileNxN()
        for i, row in enumerate(tile.rows):
            self.rows[i].copy(row)
        return self


    def __init__(self, fg: int = 0, bg: int = 0, width: int = 8, height: int = 8):
        if not width or width % 8 != 0:
            raise ValueError("width must be a multiple of 8")
        if not height or height % 8 != 0:
            raise ValueError("width must be a multiple of 8")
        self.rows: list[RowN] = [RowN(fg, bg, width) for _ in range(height)]


    def __str__(self) -> str:
        className = self.__class__.__name__
        return f'{className}({' '.join([str(x) for x in self.rows])})'


    def __len__(self) -> int:
        return len(self.rows)


    def __getitem__(self, y: int) -> RowN:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y]


    def __setitem__(self, y: int, row: RowN) -> None:
        self.rows[y] = row


    def get_pixel(self, x: int, y: int) -> int:
        if x < 0 or x > len(self[0]):
            raise IndexError('outside bounds')
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_pixel(x)


    def set_pattern(self, x: int, y: int) -> None:
        if x < 0 or x > len(self[0]):
            raise IndexError('outside bounds')
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        self.rows[y].set_pattern(x)


    def unset_pattern(self, x: int, y: int) -> None:
        if x < 0 or x > len(self[0]):
            raise IndexError('outside bounds')
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        self.rows[y].unset_pattern(x)


    def set_fg(self, y: int, index: int) -> None:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        self.rows[y].set_fg(index)


    def set_bg(self, y: int, index: int) -> None:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        self.rows[y].set_bg(index)


    def get_fg(self, y: int) -> int:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_fg()


    def get_bg(self, y: int) -> int:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_bg()


    def get_colors(self, y: int) -> tuple[int, int]:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_colors()


    def mirror_horizontally(self) -> None:
        '''mirror horizontally inplace'''
        for y in range(TILE_SIZE):
            self.rows[y].mirror()


    def mirror_vertically(self) -> None:
        tmp: list[RowN] = [RowN() for _ in range(len(self))]
        for y in range(len(self)):
            tmp[TILE_SIZE - y - 1] = self.rows[y]
        self.rows = tmp


    def shift_left(self) -> None:
        '''shift horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].shift_left()


    def shift_right(self) -> None:
        '''shift horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].shift_right()


    def shift_up(self) -> None:
        tmp: list[RowN] = [RowN() for _ in range(len(self))]
        for y in range(len(self)):
            tmp[(y - 1) % len(self)].copy(self.rows[y])
        self.rows = tmp


    def shift_down(self) -> None:
        tmp: list[RowN] = [RowN() for _ in range(len(self))]
        for y in range(len(self)):
            tmp[(y + 1) % len(self)].copy(self.rows[y])
        self.rows = tmp


    def set_copy_format(self, format: str) -> None:
        '''copy and paste data'''
        pass

