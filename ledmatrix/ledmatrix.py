#!/usr/bin/env python3
# Interface to the LED Matrix

from rpi_ws281x import PixelStrip, Color
import _rpi_ws281x as ws
from PIL import Image

from ledframe import LedFrame

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

    def begin(self):
        self.strip.begin()

    def __gammaTable(self, gamma):
        table = []
        for i in range(256):
            table.append(int((pow(i/255, gamma) * 255 + 0.5)))
        return table

    def clearScreen(self) -> None:
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, 0)
        self.strip.show()

    def loadImage(self, file: str) -> LedFrame:
        img = Image.open(file).convert("RGB")
        img.load()
        image_frame = LedFrame(img.height, img.width)
        for y in range(img.height):
            for x in range(img.width):
                pixel = img.getpixel((x,img.height - y - 1))
                image_frame.pixels.append(Color(*pixel))
        return image_frame

    def displayFrame(self, frame: LedFrame) -> None:
        if(frame.height != self.MATRIX_HEIGHT or frame.width != self.MATRIX_WIDTH):
            raise Exception("Frame is for %i x %i Matrix but we have %i x %i" % 
                (frame.width, frame.height, self.MATRIX_WIDTH, self.MATRIX_HEIGHT))
        for y in range(self.MATRIX_HEIGHT):
            for x in range(self.MATRIX_WIDTH):
                matrix_y = y
                if not x%2:
                    matrix_y = self.MATRIX_HEIGHT - y - 1
                self.strip.setPixelColor(matrix_y + x * self.MATRIX_HEIGHT, frame.pixels[frame.width*y+x])
        self.strip.show()
