#!/usr/bin/env python3
# LEDMatrix Server

import time
from rpi_ws281x import PixelStrip, Color
import _rpi_ws281x as ws
import argparse
from PIL import Image
import socket, struct, select
import itertools, sys, datetime

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

# Server Settings
UDP_IP = "0.0.0.0"
UDP_PORT = 20304
DATA_TIMEOUT_SEC = 2

# Frame constants
FRAME_IDENT = 0x1234
FRAME_HEADER_SIZE = 8
FRAME_PIXEL_SIZE = 4
FRAME_TOTAL_SIZE = FRAME_HEADER_SIZE + FRAME_PIXEL_SIZE * MATRIX_HEIGHT * MATRIX_WIDTH

def __clearScreen(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, 0)
    strip.show()

def loadImage(strip):
    img = Image.open("pattern.png").convert("RGB")
    img.load()
    for x in range(img.width):
        for y in range(img.height):
            pixel = img.getpixel((x,y))
            matrix_x = x
            matrix_y = y
            if x%2:
                matrix_y = MATRIX_HEIGHT - y - 1
            strip.setPixelColor(matrix_y + matrix_x * MATRIX_HEIGHT, Color(*pixel))
    strip.show()

def gammaTable(gamma):
    table = []
    for i in range(256):
        table.append(int((pow(i/255, gamma) * 255 + 0.5)))
    return table

def displayFrame(strip, pixels):
    for y in range(MATRIX_HEIGHT):
        for x in range(MATRIX_WIDTH):
            pixel = struct.unpack("BBB", pixels[0:3])   # Extract the first 3 bytes (R,G,B) and ignore A
            del pixels[0:4]                              # Trim the pixels array
            matrix_x = x
            matrix_y = y
            if not x%2:
                matrix_y = MATRIX_HEIGHT - y - 1
            strip.setPixelColor(matrix_y + matrix_x * MATRIX_HEIGHT, Color(*pixel))
    strip.show()

def parseFrame(data):
    (ident, height, width, length) = struct.unpack("HHHH", data[0:8])
    if(ident != FRAME_IDENT):
        raise Exception("Wrong frame ident received (got 0x%x)" % ident)
    if(height != MATRIX_HEIGHT or width != MATRIX_WIDTH):
        raise Exception("Frame is for %i x %i Matrix but we have %i x %i" % (width, height, MATRIX_WIDTH, MATRIX_HEIGHT))
    pixels = bytearray(data[8:])
    if(length != len(pixels)):
        raise Exception("Header says %i pixel bytes, but got %i" % (length, len(pixels)))
    if(length != MATRIX_HEIGHT * MATRIX_WIDTH * 4):
        raise Exception("Not enough data in the packet to make a frame")
    return pixels

def __empty_socket(sock):
    input = [sock]
    while 1:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready)==0: break
        for s in inputready: s.recv(1)


# Main program logic follows:
if __name__ == '__main__':

    gamma = gammaTable(LED_GAMMA)

    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(MATRIX_HEIGHT * MATRIX_WIDTH, LED_PIN, LED_FREQ_HZ, 
        LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_TYPE, gamma)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(DATA_TIMEOUT_SEC)

    nodata_timer = datetime.datetime.now() + datetime.timedelta(seconds = DATA_TIMEOUT_SEC)
    spinner = itertools.cycle(['-', '/', '|', '\\'])

    loadImage(strip)
    while True:
        try:
            sys.stdout.write(next(spinner))   # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char

            if(nodata_timer < datetime.datetime.now()):
                __clearScreen(strip)

            __empty_socket(sock)              # Empty the socket and wait for next frame
            data, addr = sock.recvfrom(FRAME_TOTAL_SIZE)
            try:
                pixels = parseFrame(data)
                displayFrame(strip, pixels)
                nodata_timer = datetime.datetime.now() + datetime.timedelta(seconds = DATA_TIMEOUT_SEC)
            except Exception as e:
                print("Invalid frame received: %s" % e)

        except socket.timeout:
            pass

        except KeyboardInterrupt:
            __clearScreen(strip)