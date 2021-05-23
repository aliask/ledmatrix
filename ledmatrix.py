#!/usr/bin/env python3
# Interface to the LED Matrix

import struct
from rpi_ws281x import PixelStrip, Color
import _rpi_ws281x as ws
from PIL import Image

class LEDMatrix:

    # LED strip configuration:
    MATRIX_HEIGHT = 16               # Height of the LED matrix
    MATRIX_WIDTH = 32                # Width of the LED matrix
    LED_PIN = 18                     # GPIO pin connected to the pixels (18 uses PWM, 10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ = 800000             # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10                     # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 30              # Careful not to overdrive the LEDs if using Raspberry Pi power
    LED_INVERT = False               # Invert signal (if using NPN transistor to level shift)
    LED_CHANNEL = 0                  # set to '1' for GPIOs 13, 19, 41, 45 or 53
    LED_TYPE = ws.WS2811_STRIP_GRB   # Pixel color ordering
    LED_GAMMA = 1.5                  # Brightness adjustment onto exponential curve

    def __init__(self, brightness = 30, height = 16, width = 32):
        gamma = self.__gammaTable(self.LED_GAMMA)

        self.LED_BRIGHTNESS = brightness
        self.MATRIX_HEIGHT = height
        self.MATRIX_WIDTH = width

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

    def setBrightness(self, brightness):
        self.strip.setBrightness(brightness)