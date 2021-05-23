#!/usr/bin/env python3
# LEDMatrix Server CLI Application

import datetime
import socket
import logging
import yaml

from spinner import Spinner
from ledmatrix import LEDMatrix
from udpserver import UDPServer, FrameException, NoDataException

class LEDServer:

    is_receiving = False
    config = {
        'brightness': 30,
        'height': 16,
        'width': 32,
        'udp_port': 20304,
        'data_timeout': 0.5,
        'startupImage': '/usr/share/ledserver/pattern.png'
    }

    def __reset_timer(self):
        self.nodata_timer = datetime.datetime.now() + datetime.timedelta(seconds = self.config['data_timeout'])

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
            self.config = { **self.config, **yaml.safe_load(open("/etc/ledserver.yml")) }
        except:
            logging.warning("Could not read config file, using defaults")

        try:
            leds = LEDMatrix(
                brightness = self.config['brightness'],
                height = self.config['height'],
                width = self.config['width']
            )
        except:
            logging.error("Could not initialise LED Matrix - are you root?")
            quit()

        try:
            server = UDPServer(self.config['udp_port'], self.config['data_timeout'])
            logging.info("Started listening for LED Matrix data on udp://%s:%d" % (socket.gethostname(), self.config['udp_port']))
        except:
            logging.error("Could not open UDP socket")
            quit()

        self.__reset_timer()
        leds.loadImage(self.config['startupImage'])
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

                if(packet['type'] == "frame"):
                    leds.parseFrame(*packet["frame"])
                elif(packet['type'] == "command" and packet['command'] == "brightness"):
                    logging.info("Setting brightness to %d" % packet['value'])
                    leds.setBrightness(packet['value'])

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
