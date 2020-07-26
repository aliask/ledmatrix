#!/usr/bin/env python3
# LEDMatrix Server CLI Application

import argparse
import datetime
import logging
import signal
import socket
import systemd.daemon
import time

from ledmatrix import LEDMatrix
from spinner import Spinner
from udpserver import UDPServer, FrameException, NoDataException

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
        try:
            self.leds = LEDMatrix()
        except:
            logging.error("Could not initialise LED Matrix - are you root?")
            quit(1)

        try:
            self.server = UDPServer(self.UDP_PORT, self.DATA_TIMEOUT_SEC)
            logging.info("Started listening for LED Matrix data on udp://%s:%d" % (socket.gethostname(), self.UDP_PORT))
        except:
            logging.error("Could not open UDP socket")
            quit(1)

        self.__reset_timer()

        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        systemd.daemon.notify(systemd.daemon.Notification.READY)

        try:
            self.leds.loadImage("pattern.png")
        except:
            logging.warning("Couldn't load image")

        while True:
            try:
                if(self.__has_data_stopped()):
                    logging.info("Stopped receiving data - putting display to sleep")
                    self.leds.clearScreen()

                packet = self.server.getFrame(self.leds.MATRIX_WIDTH * self.leds.MATRIX_HEIGHT)

                if(self.is_receiving is False):
                    logging.info("Receiving data from udp://%s:%s" % packet["addr"])
                    self.is_receiving = True

                self.leds.parseFrame(*packet["frame"])
                self.__reset_timer()
            except NoDataException:
                pass
            except FrameException as e:
                logging.error("Error while processing: %s" % e)


if __name__ == '__main__':
    app = LEDServer()