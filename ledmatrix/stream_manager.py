from dataclasses import dataclass
import datetime
import logging
from typing import List

from ledmatrix.ledframe import LedFrame
from ledmatrix.ledmatrix import LEDMatrix
from ledmatrix.udpserver import (
    UDPServer,
    ImageFrame,
    CommandFrame,
    Commands,
    NetworkFrame,
    NoDataException,
    FrameException,
)


DEFAULT_PRIORITY = 5
DATA_TIMEOUT_SEC = 2


@dataclass
class Stream:
    client: tuple
    priority: int
    last_packet: datetime.datetime
    is_active: bool
    buffer: List[NetworkFrame]


class StreamManager:
    streams: List[Stream]
    server: UDPServer
    leds: LEDMatrix

    def __init__(self, server: UDPServer, leds: LEDMatrix) -> None:
        self.streams = []
        self.server = server
        self.leds = leds

    def __ingest_frame(self, frame: NetworkFrame) -> None:
        # Add frame to buffer if found in existing streams
        for stream in self.streams:
            if stream.client == frame.source:
                if type(frame) is CommandFrame and frame.command == Commands.SetPriority:
                    stream.priority = frame.value
                if stream.is_active:
                    stream.buffer.append(frame)
                    stream.last_packet = datetime.datetime.now()
                return

        # Not found, create new stream for this client
        logging.debug("Received packet from new stream udp://%s:%s" % frame.source)
        new_stream = Stream(
            client=frame.source,
            priority=DEFAULT_PRIORITY,
            last_packet=datetime.datetime.now(),
            is_active=False,
            buffer=[frame],
        )
        if type(frame) is CommandFrame and frame.command == Commands.SetPriority:
            new_stream.priority = frame.value
        self.streams.append(new_stream)

    def __set_active_index(self, active_index: int) -> None:
        if active_index >= len(self.streams) or active_index < 0:
            raise IndexError
        for stream_index, stream in enumerate(self.streams):
            stream.is_active = stream_index == active_index

    def get_active_stream(self) -> Stream:
        for stream in self.streams:
            if stream.is_active:
                return stream

    def __sync_clients(self) -> None:
        """Removes stale clients, and sets the is_active property based on stream priority. If no streams remain, clear the LEDs"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=DATA_TIMEOUT_SEC)
        # Remove streams that have timed out
        self.streams = [stream for stream in self.streams if stream.last_packet > cutoff_time]

        if len(self.streams) == 0:
            logging.info("Stopped receiving data - putting display to sleep")
            self.leds.clearScreen()
            return

        # Sort the streams by priority, then currently active. This way the current stream stays active, unless a higher priority one joins
        self.streams = sorted(self.streams, key=lambda x: (x.priority, x.is_active), reverse=True)
        self.__set_active_index(active_index=0)

    def __get_next_frame(self) -> None:
        stream = self.get_active_stream()
        if stream and len(stream.buffer):
            return stream.buffer.pop(0)
        else:
            return None

    def __process_frame(self, network_frame: NetworkFrame) -> None:
        if type(network_frame) is ImageFrame:
            # Take received packet and format for LED panel
            frame = LedFrame(network_frame.height, network_frame.width)
            frame.fill_from_bytearray(network_frame.pixels)
            self.leds.displayFrame(frame)
        elif type(network_frame) is CommandFrame:
            if network_frame.command == Commands.SetBrightness:
                logging.info(f"Setting brightness to {network_frame.value}")
                self.leds.setBrightness(network_frame.value)
            elif network_frame.command == Commands.SetPriority:
                pass
            else:
                logging.warning(f"Unkown Command received ({network_frame.command:x})")

    def run(self) -> None:
        try:
            frame_pixels = self.leds.MATRIX_WIDTH * self.leds.MATRIX_HEIGHT
            network_frame = self.server.get_frame(frame_pixels)
            self.__ingest_frame(network_frame)
            self.__sync_clients()
            next_active_frame = self.__get_next_frame()
            if next_active_frame:
                self.__process_frame(next_active_frame)
        except NoDataException:
            self.__sync_clients()
        except FrameException as e:
            logging.error("Error while processing: %s" % e)
            pass
