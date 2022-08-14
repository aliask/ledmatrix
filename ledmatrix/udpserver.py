#!/usr/bin/env python3
# Listener for Frame Data

import logging, socket, struct, select
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

class FrameException(Exception):
    pass

class NoDataException(Exception):
    pass

class Commands(Enum):
    SetBrightness = 0

@dataclass
class NetworkFrame:
    source: Any = field(default=None, init=False)

@dataclass
class CommandFrame(NetworkFrame):
    IDENT = 0x4321

    command: Commands
    value: int

@dataclass
class ImageFrame(NetworkFrame):
    IDENT = 0x1234

    pixels: bytearray
    height: int
    width: int

class UDPServer:

    ALL_IFACES = "0.0.0.0"
    FRAME_HEADER_SIZE = 8
    FRAME_PIXEL_SIZE = 4

    def __init__(self, port: int, timeout: int) -> None:
        self.port = port
        self.timeout = timeout

    def start(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ALL_IFACES, self.port))
        self.sock.settimeout(self.timeout)

    def __empty_socket(self) -> None:
        input = [self.sock]
        while 1:
            inputready, o, e = select.select(input,[],[], 0.0)
            if len(inputready)==0: break
            for s in inputready: s.recv(1)

    def __parse_command(self, data) -> CommandFrame:
        (command, value) = struct.unpack("BB", data)

        if(command == Commands.SetBrightness.value):
            return CommandFrame(command=Commands.SetBrightness, value=value)
        else:
            raise FrameException("Unknown command received: 0x%x" % command)

    def __parse_image(self, data, num_pixels) -> ImageFrame:
        (height, width, length) = struct.unpack("HHH", data[0:6])
        pixels = bytearray(data[6:])

        if(length != len(pixels)):
            raise FrameException("Header says %i pixel bytes, but got %i" % (length, len(pixels)))

        if(length != num_pixels * self.FRAME_PIXEL_SIZE):
            raise FrameException("Not enough data in the packet to make a frame")

        return ImageFrame(height=height, width=width, pixels=pixels)

    def get_frame(self, num_pixels: int) -> NetworkFrame:
        num_bytes = num_pixels * self.FRAME_PIXEL_SIZE + self.FRAME_HEADER_SIZE
        logging.debug("Emptying socking before RX")
        self.__empty_socket()
        try:
            logging.debug("Waiting for new packet")
            data, addr = self.sock.recvfrom(num_bytes)

            try:
                addr = socket.getnameinfo(addr, 0)
            except socket.gaierror:
                logging.warn("Error during hostname lookup for %s" % addr[0])

            frame_type = struct.unpack("H", data[0:2])[0]
            if(frame_type == CommandFrame.IDENT):
                parsed = self.__parse_command(data[2:])
            elif(frame_type == ImageFrame.IDENT):
                parsed = self.__parse_image(data[2:], num_pixels)
            else:
                raise FrameException("Unknown frame identity: 0x%x" % frame_type)

            parsed.source = addr
            return parsed

        except socket.timeout:
            raise NoDataException(socket.timeout)
