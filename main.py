#!/usr/bin/env python3
# LEDMatrix Server CLI Application

# Activate the virtual environment inside Python to allow simple execution
import os
base_dir = os.path.dirname(os.path.realpath(os.path.expanduser(__file__)))
activate_this = os.path.join(base_dir, 'venv/bin/activate_this.py')
exec(open(activate_this).read())

import argparse
import datetime
import logging
import signal
import socket
import systemd.daemon
import time
import struct

from itertools import zip_longest
from rpi_ws281x import Color

from ledmatrix import *

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)

class LEDServer:

    UDP_PORT = 20304
    DATA_TIMEOUT_SEC = 0.5
    is_receiving = False

    def __reset_timer(self):
        self.nodata_timer = datetime.datetime.now() + datetime.timedelta(seconds = self.DATA_TIMEOUT_SEC)

    def __has_data_stopped(self):
        timedout = self.nodata_timer < datetime.datetime.now()
        if(timedout and self.is_receiving):
            self.is_receiving = False
            return True
        else:
            return False

    def __graceful_exit(self):
        logging.info("Shutting down")
        self.leds.clearScreen()
        systemd.daemon.notify(systemd.daemon.Notification.STOPPING)
        quit(0)

    def handle_signal(self, signum, frame):
        logging.info("Caught %s" % signal.Signals(signum).name)
        self.__graceful_exit()

    def __init__(self):
        logging.basicConfig(level = logging.INFO)
        self.leds = LEDMatrix()
        self.server = UDPServer(self.UDP_PORT, self.DATA_TIMEOUT_SEC)
        self.__reset_timer()

    def run(self):
        try:
            self.leds.begin()
        except:
            logging.error("Could not initialise LED Matrix - are you root?")
            quit(1)

        try:
            self.server.start()
            logging.info("Started listening for LED Matrix data on udp://%s:%d" % (socket.gethostname(), self.UDP_PORT))
        except:
            logging.error("Could not open UDP socket")
            quit(1)

        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        systemd.daemon.notify(systemd.daemon.Notification.READY)

        try:
            image = self.leds.loadImage(os.path.join(base_dir, 'pattern.png'))
            self.leds.displayFrame(image)
        except:
            logging.warning("Couldn't load image")

        while True:
            try:
                if(self.__has_data_stopped()):
                    logging.info("Stopped receiving data - putting display to sleep")
                    self.leds.clearScreen()

                frame_pixels = self.leds.MATRIX_WIDTH * self.leds.MATRIX_HEIGHT
                packet = self.server.getFrame(frame_pixels)

                logging.debug("Received packet")

                if(self.is_receiving is False):
                    logging.info("Receiving data from udp://%s:%s" % packet["addr"])
                    self.is_receiving = True

                # Take received packet and format for LED panel
                (height,width,pixels) = packet["frame"]
                frame = LedFrame(height,width)
                for pixel in grouper(4, list(struct.unpack('B'*frame_pixels*4, pixels))):
                    (r,g,b,a) = pixel
                    frame.pixels.append(Color(r,g,b))

                self.leds.displayFrame(frame)
                self.__reset_timer()
            except NoDataException:
                pass
            except FrameException as e:
                logging.error("Error while processing: %s" % e)


if __name__ == '__main__':
    app = LEDServer()
    app.run()
