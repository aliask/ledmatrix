from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import struct


class FrameException(Exception):
    pass


class Command(Enum):
    SetBrightness = 0
    SetPriority = 1


@dataclass
class NetworkFrame(ABC):
    source: tuple = field(default_factory=tuple, init=False)
    IDENT = 0x0000

    @abstractmethod
    def as_binary(self):
        pass

    @classmethod
    @abstractmethod
    def from_bytes(cls, source_bytes: bytes) -> NetworkFrame:
        pass


@dataclass
class CommandFrame(NetworkFrame):
    command: Command
    value: int
    IDENT: int = field(repr=False, init=False, default=0x4321)

    def as_binary(self):
        return struct.pack("HBB", self.IDENT, self.command, self.value)

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        if len(source_bytes) != 4:
            raise FrameException("Cannot parse command frame, data is not 4 bytes long")

        (ident, command, value) = struct.unpack("HBB", source_bytes)

        if ident != cls.IDENT:
            raise FrameException(f"Cannot parse command frame, IDENT should be 0x{cls.IDENT:x} but got 0x{ident:x}")

        try:
            command_parsed = Command(command)
        except ValueError:
            raise FrameException(f"Cannot parse command frame, got unknown command type ({command})")

        return cls(command=command_parsed, value=value)


@dataclass
class ImageFrame(NetworkFrame):
    height: int
    width: int
    pixels: bytes = field(repr=False)
    IDENT: int = field(repr=False, init=False, default=0x1234)
    PIXEL_SIZE: int = field(repr=False, init=False, default=4)
    HEADER_SIZE: int = field(repr=False, init=False, default=8)

    @property
    def header(self) -> bytes:
        return struct.pack("HHHH", self.IDENT, self.height, self.width, len(self.pixels))

    def as_binary(self):
        return self.header + self.pixels

    @classmethod
    def from_bytes(cls, source_bytes: bytes):
        (ident, height, width, pixeldata_size) = struct.unpack("HHHH", source_bytes[0 : cls.HEADER_SIZE])

        if ident != cls.IDENT:
            raise FrameException(f"Cannot parse image frame, IDENT should be 0x{cls.IDENT:x} but got 0x{ident:x}")

        expected_pixeldata_size = height * width * cls.PIXEL_SIZE
        if pixeldata_size != expected_pixeldata_size:
            raise FrameException(
                f"Cannot parse image frame, pixeldata length mismatch - expected {expected_pixeldata_size} bytes but got {pixeldata_size}"
            )

        return cls(width=width, height=height, pixels=source_bytes[cls.HEADER_SIZE :])


def parse_frame(source_bytes: bytes) -> NetworkFrame:
    frame_type = struct.unpack("H", source_bytes[0:2])[0]
    for cls in NetworkFrame.__subclasses__():
        if frame_type == cls.IDENT:
            return cls.from_bytes(source_bytes=source_bytes)
    raise FrameException(f"Unknown frame IDENT (0x{frame_type:x})")
