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


# classes
class RowN:
    pattern: list[bool]
    fg: list[int]
    bg: list[int]

    def __init__(self, fg: int = 0, bg: int = 0, width: int = 8):
        if width % 8 != 0:
            raise ValueError("width must be a multiple of 8")
        self.pattern = [False] * width
        self.fg = [fg] * (width // TILE_SIZE)
        self.bg = [bg] * (width // TILE_SIZE)


    def __str__(self) -> str:
        s = ''
        for x in range(0, len(self) // 8):
            bin = ''
            for value in self.pattern[x * 8: (x + 1) * 8]:
                bin += '1' if value else '0'
            s += f'(p:{bin},c:{hex(self.fg[x])}:{hex(self.bg[x])})\n'
        return s


    def __len__(self) -> int:
        return len(self.pattern)


    def __getitem__(self, x: int) -> int:
        """Return the foreground color index if the pixel is active, otherwise return the background color index."""
        return self.fg[x // TILE_SIZE] if self.pattern[x] else self.bg[x // TILE_SIZE]


    def copy(self, row: RowN) -> None:
        self.pattern = list(row.pattern)
        self.fg, self.bg = list(row.fg), list(row.bg)


    def set_fg(self, x: int | None, fg: int) -> None:
        if x == None:
            self.fg = [fg] * (len(self) // TILE_SIZE)
        else:
            if x < 0 or x > len(self):
                raise IndexError('outside bounds')
            self.fg[x // TILE_SIZE] = fg


    def get_pixel(self, x: int) -> bool:
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        return self.pattern[x]


    def set_pattern(self, x: int) -> None:
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        self.pattern[x] = True


    def unset_pattern(self, x: int) -> None:
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        self.pattern[x] = False


    def set_bg(self, x: int | None, bg: int) -> None:
        if x == None:
            self.bg = [bg] * (len(self) // TILE_SIZE)
        else:
            if x < 0 or x > len(self):
                raise IndexError('outside bounds')
            self.bg[x // TILE_SIZE] = bg


    def get_fg(self, x: int) -> int:
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        return self.fg[x // TILE_SIZE]


    def get_bg(self, x: int) -> int:
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        return self.bg[x // TILE_SIZE]


    def get_colors(self, x: int) -> tuple[int, int]:
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        return self.fg[x // TILE_SIZE], self.bg[x // TILE_SIZE]


    def invert(self, x: int) -> None:
        '''Invert pattern inplace'''
        if x < 0 or x > len(self):
            raise IndexError('outside bounds')
        x = x // TILE_SIZE
        for x in range(x * TILE_SIZE, (x + 1) * TILE_SIZE):
            self.pattern[x] = not self.pattern[x]


    def mirror(self) -> None:
        '''mirror pattern inplace'''
        self.fg = list(reversed(self.fg))
        self.bg = list(reversed(self.bg))
        self.pattern = list(reversed(self.pattern))


    def shift_left(self, times: int = 1) -> None:
        '''shift left inplace'''
        for i in range(times):
            self.pattern.append(self.pattern.pop(0))


    def shift_tile_left(self) -> None:
        '''shift left 8 times inplace'''
        self.shift_left(TILE_SIZE)
        self.fg.append(self.fg.pop(0))
        self.bg.append(self.bg.pop(0))


    def shift_right(self, times: int = 1) -> None:
        '''shift right inplace'''
        for i in range(times):
            self.pattern.insert(0, self.pattern.pop())


    def shift_tile_right(self) -> None:
        '''shift right 8 times inplace'''
        self.shift_right(TILE_SIZE)
        self.fg.insert(0, self.fg.pop())
        self.bg.insert(0, self.bg.pop())


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


    def set_fg(self, x: int | None, y: int, index: int) -> None:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        self.rows[y].set_fg(x, index)


    def set_bg(self, x: int | None, y: int, index: int) -> None:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        self.rows[y].set_bg(x, index)


    def get_fg(self, x: int, y: int) -> int:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_fg(x)


    def get_bg(self, x: int, y: int) -> int:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_bg(x)


    def get_colors(self, x: int, y: int) -> tuple[int, int]:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y].get_colors(x)


    def mirror_horizontally(self) -> None:
        '''mirror horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].mirror()


    def mirror_vertically(self) -> None:
        tmp: list[RowN] = [RowN() for _ in range(len(self))]
        for y in range(len(self)):
            tmp[len(self) - y - 1] = self.rows[y]
        self.rows = tmp


    def shift_left(self, times: int = 1) -> None:
        '''shift horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].shift_left(times)


    def shift_tile_left(self) -> None:
        '''shift horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].shift_tile_left()


    def shift_right(self) -> None:
        '''shift horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].shift_right()


    def shift_tile_right(self) -> None:
        '''shift horizontally inplace'''
        for y in range(len(self)):
            self.rows[y].shift_tile_right()


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

