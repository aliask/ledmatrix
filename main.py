#!/usr/bin/env python3
# LEDMatrix Server CLI Application

import os
import logging
import signal

from ledmatrix import *


class LEDServer:

    LEDSERVER_PORT = int(os.environ.get("LEDSERVER_PORT", 20304))
    DATA_TIMEOUT_SEC = 3

    def __graceful_exit(self):
        logging.info("Shutting down")
        self.leds.clearScreen()
        quit(0)

    def handle_signal(self, signum, frame):
        logging.info("Caught %s" % signal.Signals(signum).name)
        self.__graceful_exit()

    def __init__(self):
        logging.basicConfig(
            format="%(asctime)s [%(levelname)-8s] %(message)s",
            level=logging.INFO,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.leds = LEDMatrix()
        self.stream_manager = StreamManager(port=self.LEDSERVER_PORT, timeout=self.DATA_TIMEOUT_SEC, leds=self.leds)

    def run(self):
        try:
            self.leds.begin()
        except Exception as e:
            logging.error(f"Could not initialise LED Matrix - are you root? ({e})")
            exit(1)

        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        try:
            image = self.leds.loadImage("/app/pattern.png")
            self.leds.displayFrame(image)
        except:
            logging.warning("Couldn't load image")

        self.stream_manager.run()


if __name__ == "__main__":
    app = LEDServer()
    app.run()
