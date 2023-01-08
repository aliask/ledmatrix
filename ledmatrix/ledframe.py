# LedFrame dataclass

from dataclasses import dataclass, field
from itertools import zip_longest
import struct

from rpi_ws281x import Color


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


@dataclass
class LedFrame:
    height: int
    width: int
    pixels: list = field(default_factory=list)

    def fill_from_bytes(self, pixeldata: bytes):
        self.pixels = []
        pixel_list = list(struct.unpack("B" * self.height * self.width * 4, pixeldata))
        for pixel in grouper(4, pixel_list):
            (r, g, b, a) = pixel
            self.pixels.append(Color(r, g, b))

