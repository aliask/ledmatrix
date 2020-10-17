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

    def __init__(self):
        self.leds = LEDMatrix()
        self.server = UDPServer(self.UDP_PORT, self.DATA_TIMEOUT_SEC)

    def run():
        logging.basicConfig(level = logging.INFO)

        try:
            leds.run()
        except e: # try to narrow?
            logging.error("Could not initialise LED Matrix - are you root?")
            raise e

        try:
            server.run()
            logging.info("Started listening for LED Matrix data on udp://%s:%d" % (socket.gethostname(), self.UDP_PORT))
        except e: # try to narrow?
            logging.error("Could not open UDP socket")
            raise e

        self.__reset_timer()

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        systemd.daemon.notify(systemd.daemon.Notification.READY)

        try:
            self.leds.loadImage("pattern.png")
        except: # narrow exception
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
        
    
    def _handle_signal(self, signum, frame):
        logging.info("Caught %s" % signal.Signals(signum).name)
        self.__graceful_exit()

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

if __name__ == '__main__':
    app = LEDServer()
    app.run()