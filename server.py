#!/usr/bin/env python3
# LEDMatrix Server

import time
from rpi_ws281x import PixelStrip, Color
import _rpi_ws281x as ws
import argparse
from PIL import Image
import socket, struct, select
import itertools, sys, datetime


class LEDMatrix:

    # LED strip configuration:
    MATRIX_HEIGHT = 16               # Height of the LED matrix
    MATRIX_WIDTH = 32                # Width of the LED matrix
    LED_PIN = 18                     # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ = 800000             # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10                     # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 30              # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False               # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0                  # set to '1' for GPIOs 13, 19, 41, 45 or 53
    LED_TYPE = ws.WS2811_STRIP_GRB   # Pixel color ordering
    LED_GAMMA = 1.5                  # Brightness adjustment onto exponential curve

    def __init__(self):
        gamma = self.__gammaTable(self.LED_GAMMA)

        self.strip = PixelStrip(
            num = self.MATRIX_HEIGHT * self.MATRIX_WIDTH,
            pin = self.LED_PIN,
            freq_hz = self.LED_FREQ_HZ, 
            dma = self.LED_DMA,
            invert = self.LED_INVERT,
            brightness = self.LED_BRIGHTNESS,
            channel = self.LED_CHANNEL,
            strip_type = self.LED_TYPE,
            gamma = gamma
        )
        self.strip.begin()

    def __gammaTable(self, gamma):
        table = []
        for i in range(256):
            table.append(int((pow(i/255, gamma) * 255 + 0.5)))
        return table

    def clearScreen(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, 0)
        self.strip.show()

    def loadImage(self, file):
        img = Image.open(file).convert("RGB")
        img.load()
        for x in range(img.width):
            for y in range(img.height):
                pixel = img.getpixel((x,y))
                matrix_x = x
                matrix_y = y
                if x%2:
                    matrix_y = self.MATRIX_HEIGHT - y - 1
                self.strip.setPixelColor(matrix_y + matrix_x * self.MATRIX_HEIGHT, Color(*pixel))
        self.strip.show()

    def __displayFrame(self, pixels):
        for y in range(self.MATRIX_HEIGHT):
            for x in range(self.MATRIX_WIDTH):
                pixel = struct.unpack("BBB", pixels[0:3])   # Extract the first 3 bytes (R,G,B) and ignore A
                del pixels[0:4]                             # Trim the pixels array
                matrix_x = x
                matrix_y = y
                if not x%2:
                    matrix_y = self.MATRIX_HEIGHT - y - 1
                self.strip.setPixelColor(matrix_y + matrix_x * self.MATRIX_HEIGHT, Color(*pixel))
        self.strip.show()

    def parseFrame(self, height, width, pixels):
        if(height != self.MATRIX_HEIGHT or width != self.MATRIX_WIDTH):
            raise Exception("Frame is for %i x %i Matrix but we have %i x %i" % 
                (width, height, self.MATRIX_WIDTH, self.MATRIX_HEIGHT))
        self.__displayFrame(pixels)


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
        data, addr = self.sock.recvfrom(num_bytes)
        (ident, height, width, length) = struct.unpack("HHHH", data[0:8])
        if(ident != self.FRAME_IDENT):
            raise Exception("Wrong frame ident received (got 0x%x)" % ident)
        pixels = bytearray(data[8:])
        if(length != len(pixels)):
            raise Exception("Header says %i pixel bytes, but got %i" % (length, len(pixels)))
        if(length != num_pixels * self.FRAME_PIXEL_SIZE):
            raise Exception("Not enough data in the packet to make a frame")
        return (height, width, pixels)


class LEDServer:

    UDP_PORT = 20304
    DATA_TIMEOUT_SEC = 2

    spinner = itertools.cycle(['🕛', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚'])

    def __spin(self):
        sys.stdout.write(next(self.spinner))
        sys.stdout.flush()
        sys.stdout.write('\b\b')

    def __reset_timer(self):
        self.nodata_timer = datetime.datetime.now() + datetime.timedelta(seconds = self.DATA_TIMEOUT_SEC)

    def main(self):
        leds = LEDMatrix()
        server = UDPServer(self.UDP_PORT, self.DATA_TIMEOUT_SEC)

        self.__reset_timer()
        leds.loadImage("pattern.png")
        while True:
            try:
                self.__spin()

                if(self.nodata_timer < datetime.datetime.now()):
                    leds.clearScreen()

                frame = server.getFrame(leds.MATRIX_WIDTH * leds.MATRIX_HEIGHT)
                leds.parseFrame(*frame)
                self.__reset_timer()
            except socket.timeout:
                pass
            except KeyboardInterrupt:
                leds.clearScreen()
                quit()
            except Exception as e:
                print("Error while processing: %s" % e)


if __name__ == '__main__':

    app = LEDServer()
    app.main()
