#!/usr/bin/env python3
# LEDMatrix Server CLI Application

import time

import argparse
import datetime
import socket
import logging

from spinner import Spinner
from ledmatrix import LEDMatrix
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

    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
        spinner = Spinner()

        try:
            leds = LEDMatrix()
        except:
            logging.error("Could not initialise LED Matrix - are you root?")
            quit()

        try:
            server = UDPServer(self.UDP_PORT, self.DATA_TIMEOUT_SEC)
            logging.info("Started listening for LED Matrix data on udp://%s:%d" % (socket.gethostname(), self.UDP_PORT))
        except:
            logging.error("Could not open UDP socket")
            quit()

        self.__reset_timer()
        leds.loadImage("pattern.png")
        while True:
            try:
                spinner.spin()

                if(self.__has_data_stopped()):
                    logging.info("Stopped receiving data - putting display to sleep")
                    leds.clearScreen()

                packet = server.getFrame(leds.MATRIX_WIDTH * leds.MATRIX_HEIGHT)

                if(self.is_receiving is False):
                    logging.info("Receiving data from udp://%s:%s" % packet["addr"])
                    self.is_receiving = True

                leds.parseFrame(*packet["frame"])
                self.__reset_timer()
            except NoDataException:
                pass
            except KeyboardInterrupt:
                logging.info("Caught keyboard interrupt, shutting down")
                leds.clearScreen()
                quit()
            except FrameException as e:
                logging.error("Error while processing: %s" % e)


if __name__ == '__main__':
    app = LEDServer()