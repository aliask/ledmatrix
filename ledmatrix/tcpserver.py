#!/usr/bin/env python3
# Listener for Frame Data

import logging, socket, struct
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable
import socketserver


class FrameException(Exception):
    pass


class NoDataException(Exception):
    pass


class Commands(Enum):
    SetBrightness = 0
    SetPriority = 1


@dataclass
class NetworkFrame:
    source: tuple = field(default_factory=tuple, init=False)

    def as_binary(self):
        raise NotImplementedError


@dataclass
class CommandFrame(NetworkFrame):
    command: Commands
    value: int
    IDENT = 0x4321

    def as_binary(self):
        return struct.pack("HBB", self.IDENT, self.command, self.value)


@dataclass
class ImageFrame(NetworkFrame):
    pixels: bytearray
    height: int
    width: int
    IDENT = 0x1234

    def as_binary(self):
        header = struct.pack("HHHH", self.IDENT, self.height, self.width, len(self.pixels))
        return header + self.pixels


class TCPServer:

    ALL_IFACES = "0.0.0.0"
    FRAME_HEADER_SIZE = 8
    FRAME_PIXEL_SIZE = 4

    def __init__(self, port: int, timeout: int, pixels: int) -> None:
        self.port = port
        self.timeout = timeout
        self.pixels = pixels

    @property
    def frame_size(self) -> int:
        return self.FRAME_HEADER_SIZE + self.pixeldata_size

    @property
    def pixeldata_size(self) -> int:
        return self.FRAME_PIXEL_SIZE * self.pixels

    def run(self, handler: Callable[[NetworkFrame], None], service_actions: Callable[[None], None]):
        
        class PacketHandler(socketserver.BaseRequestHandler):

            def __parse_command(pkself, data) -> CommandFrame:
                (command, value) = struct.unpack("BB", data)

                try:
                    return CommandFrame(command=Commands(command), value=value)
                except ValueError as e:
                    raise FrameException("Unknown command received: 0x%x" % command, e)

            def __parse_image(pkself, data) -> ImageFrame:
                (height, width, length) = struct.unpack("HHH", data[0:6])
                pixels = bytearray(data[6:])

                if length != self.pixeldata_size:
                    raise FrameException(f"Header says {length} pixel bytes, but we need {self.pixeldata_size}")
                if length != len(pixels):
                    raise FrameException(f"Header says {length} pixel bytes, but we got {len(pixels)}")

                return ImageFrame(height=height, width=width, pixels=pixels)

            def handle(pkself):
                # Reassemble TCP packets
                data = b""
                while True:
                    new_data = pkself.request.recv(1024)
                    if not new_data:
                        break
                    data += new_data

                if not data:
                    return

                addr = pkself.client_address

                try:
                    addr = socket.getnameinfo(pkself.client_address, 0)
                except socket.gaierror:
                    logging.warn("Error during hostname lookup for %s" % addr[0])

                frame_type = struct.unpack("H", data[0:2])[0]
                if frame_type == CommandFrame.IDENT:
                    parsed = pkself.__parse_command(data[2:])
                elif frame_type == ImageFrame.IDENT:
                    parsed = pkself.__parse_image(data[2:])
                else:
                    raise FrameException("Unknown frame identity: 0x%x" % frame_type)

                parsed.source = addr
                handler(parsed)
        
        logging.info(f"Starting TCP Server on {self.ALL_IFACES}:{self.port}")
        with socketserver.TCPServer((self.ALL_IFACES, self.port), PacketHandler) as server:
            server.service_actions = service_actions
            server.serve_forever()
