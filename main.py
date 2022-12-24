#!/usr/bin/env python3
# LEDMatrix Server CLI Application

import os
import datetime
import logging
import signal
import socket

from ledmatrix import *




class LEDServer:

    UDP_PORT = int(os.environ.get("LEDSERVER_PORT", 20304))
    DATA_TIMEOUT_SEC = 2
    is_receiving = True

    def __reset_timer(self):
        self.nodata_timer = datetime.datetime.now() + datetime.timedelta(
            seconds=self.DATA_TIMEOUT_SEC
        )

    def __has_data_stopped(self):
        timedout = self.nodata_timer < datetime.datetime.now()
        if timedout and self.is_receiving:
            self.is_receiving = False
            return True
        else:
            return False

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
            logging.info(
                "Started listening for LED Matrix data on udp://%s:%d"
                % (socket.gethostname(), self.UDP_PORT)
            )
        except:
            logging.error("Could not open UDP socket")
            quit(1)

        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        try:
            image = self.leds.loadImage("/app/pattern.png")
            self.leds.displayFrame(image)
        except:
            logging.warning("Couldn't load image")

        while True:
            try:
                if self.__has_data_stopped():
                    logging.info("Stopped receiving data - putting display to sleep")
                    self.leds.clearScreen()

                frame_pixels = self.leds.MATRIX_WIDTH * self.leds.MATRIX_HEIGHT
                network_frame = self.server.get_frame(frame_pixels)

                logging.debug("Received packet")

                if self.is_receiving is False:
                    logging.info("Receiving data from udp://%s:%s" % network_frame.source)
                    self.is_receiving = True

                if type(network_frame) is ImageFrame:
                    # Take received packet and format for LED panel
                    frame = LedFrame(network_frame.height, network_frame.width)
                    frame.fill_from_bytearray(network_frame.pixels)
                    self.leds.displayFrame(frame)
                elif type(network_frame) is CommandFrame and \
                        network_frame.command == Commands.SetBrightness:
                    logging.info("Setting brightness to %d" % network_frame.value)
                    self.leds.setBrightness(network_frame.value)

                self.__reset_timer()

            except NoDataException:
                pass
            except FrameException as e:
                logging.error("Error while processing: %s" % e)


if __name__ == "__main__":
    app = LEDServer()
    app.run()
