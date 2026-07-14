from __future__ import annotations  # 1. Add this at the top
from typing import Self

from v9918 import divide_colors


TILE_SIZE = 8


# Disable debug
debug = lambda *args : None


#
# Classes
#

class TileRow:
    pattern: list[bool]
    fg: list[int]
    bg: list[int]

    def __init__(self, pattern: list[bool] | None = None, fg: list[int] | None = None, bg: list[int] | None = None, width: int = 8):
        if width % 8 != 0:
            raise ValueError("width must be a multiple of 8")
        n = width // TILE_SIZE
        self.pattern = [False] * width if pattern is None else pattern
        debug(f'{self.pattern=}')
        self.fg = [0] * n if fg is None else fg[0:n]
        self.bg = [0] * n if bg is None else bg[0:n]


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


    def copy(self, row: Self) -> None:
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


class Tile:
    rows: list[TileRow]

    @staticmethod
    def copy(tile: Self) -> Self:
        self = Tile()
        for i, row in enumerate(tile.rows):
            self.rows[i].copy(row)
        return self


    def __init__(self, pattern: list[bool] | None = None, fg: list[int] | None = None, bg: list[int] | None = None, width: int = 8, height: int = 8):
        if not width or width % 8 != 0:
            raise ValueError("width must be a multiple of 8")
        if not height or height % 8 != 0:
            raise ValueError("height must be a multiple of 8")

        print(f'{width=}, {height=}')
        self.rows = [TileRow(pattern[n * width : n * width + 8],
                     fg[n : n + 1], bg[n : n + 1], width) for n in range(height)]


    def __str__(self) -> str:
        className = self.__class__.__name__
        return f'{className}({' '.join([str(x) for x in self.rows])})'


    def __len__(self) -> int:
        return len(self.rows)


    def __getitem__(self, y: int) -> TileRow:
        if y < 0 or y > len(self):
            raise IndexError('outside bounds')
        return self.rows[y]


    def __setitem__(self, y: int, row: TileRow) -> None:
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
        tmp: list[TileRow] = [TileRow() for _ in range(len(self))]
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
        tmp: list[TileRow] = [TileRow() for _ in range(len(self))]
        for y in range(len(self)):
            tmp[(y - 1) % len(self)].copy(self.rows[y])
        self.rows = tmp


    def shift_down(self) -> None:
        tmp: list[TileRow] = [TileRow() for _ in range(len(self))]
        for y in range(len(self)):
            tmp[(y + 1) % len(self)].copy(self.rows[y])
        self.rows = tmp


    def set_copy_format(self, format: str) -> None:
        '''copy and paste data'''
        pass


#
# functions
#

def get_pattern(pattern: int, bit: int) -> bool:
    return True if pattern & (1 << (TILE_SIZE - 1 - bit)) else False


def from_105_to_metatile(data: list[int], width: int, height: int) -> Tile:
    p0, fg, bg = [], [], []
    i = iter(data)
    while True:
        b = next(i, None)
        if b is None: break
        p0.extend([get_pattern(b, bit) for bit in range(8)])
        b = next(i)
        c = divide_colors(b)
        fg.append(c[0])
        bg.append(c[1])
    debug('l: pg0, fg, bg', len(p0), len(fg), len(bg))
    debug('v: pg0, fg, bg', p0, fg, bg)

    return Tile(p0, fg, bg, width, height)
