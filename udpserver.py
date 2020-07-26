#!/usr/bin/env python3
# Listener for Frame Data

import socket, struct, select

class FrameException(Exception):
    pass

class NoDataException(Exception):
    pass

class UDPServer:

    ALL_IFACES = "0.0.0.0"
    FRAME_IDENT = 0x1234
    FRAME_HEADER_SIZE = 8
    FRAME_PIXEL_SIZE = 4

    def __init__(self, port, timeout):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ALL_IFACES, port))
        self.sock.settimeout(timeout)

    def __empty_socket(self):
        input = [self.sock]
        while 1:
            inputready, o, e = select.select(input,[],[], 0.0)
            if len(inputready)==0: break
            for s in inputready: s.recv(1)

    def getFrame(self, num_pixels):
        num_bytes = num_pixels * self.FRAME_PIXEL_SIZE + self.FRAME_HEADER_SIZE
        self.__empty_socket()
        try:
            data, addr = self.sock.recvfrom(num_bytes)
            addr = socket.getnameinfo(addr, 0)
            (ident, height, width, length) = struct.unpack("HHHH", data[0:8])
            if(ident != self.FRAME_IDENT):
                raise FrameException("Wrong frame ident received (got 0x%x)" % ident)
            pixels = bytearray(data[8:])
            if(length != len(pixels)):
                raise FrameException("Header says %i pixel bytes, but got %i" % (length, len(pixels)))
            if(length != num_pixels * self.FRAME_PIXEL_SIZE):
                raise FrameException("Not enough data in the packet to make a frame")
            packet = { 
                "addr": addr, 
                "frame": (height, width, pixels)
            }
            return packet
        except socket.timeout:
            raise NoDataException(socket.timeout)
