from dataclasses import dataclass, field
import datetime
import logging
from typing import List

from ledmatrix.ledframe import LedFrame
from ledmatrix.ledmatrix import LEDMatrix
from ledmatrix.tcpserver import (
    TCPServer,
    ImageFrame,
    CommandFrame,
    Commands,
    NetworkFrame,
    NoDataException,
    FrameException,
)


DEFAULT_PRIORITY = 5
DATA_TIMEOUT_SEC = 3


@dataclass
class Stream:
    client: tuple
    priority: int
    last_packet: datetime.datetime
    is_active: bool
    buffer: List[NetworkFrame] = field(repr=False, default_factory=list)


class StreamManager:
    streams: List[Stream]
    server: TCPServer
    leds: LEDMatrix

    def __init__(self, port: int, timeout: int, leds: LEDMatrix) -> None:
        self.streams = []
        self.leds = leds
        frame_pixels = self.leds.MATRIX_WIDTH * self.leds.MATRIX_HEIGHT
        self.server = TCPServer(port=port, timeout=timeout, pixels=frame_pixels)

    def __ingest_frame(self, frame: NetworkFrame) -> None:
        """Add frame to buffer if found in existing streams"""
        logging.debug(f"__ingest_frame(frame={frame})")
        for stream in self.streams:
            if stream.client == frame.source[0]:
                logging.debug(f"[Stream {stream.client}] Adding frame to buffer)")
                stream.buffer.append(frame)
                stream.last_packet = datetime.datetime.now()
                return

        # Not found, create new stream for this client
        logging.info(f"[Stream {frame.source[0]}] Received frame from new source - tcp://{frame.source[0]}:{frame.source[1]}")
        new_stream = Stream(
            client=frame.source[0],
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
            if stream_index == active_index and stream.is_active == False:
                logging.info(f"[Stream {stream.client}] I'm the captain now")
                stream.is_active = True
            elif stream_index != active_index and stream.is_active == True:
                logging.info(f"[Stream {stream.client}] kthxbai")
                stream.is_active = False

    def get_active_stream(self) -> Stream:
        for stream in self.streams:
            if stream.is_active:
                return stream

    def __sync_clients(self) -> None:
        """Removes stale clients, and sets the is_active property based on stream priority. If no streams remain, clear the LEDs"""
        logging.debug("__sync_clients()")
        # No clients to sync.
        if len(self.streams) == 0:
            return

        cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=DATA_TIMEOUT_SEC)
        # Remove streams that have timed out
        for stream in self.streams.copy():
            if stream.last_packet <= cutoff_time:
                self.streams.remove(stream)
                logging.info(f"[Stream {stream.client}] Timed out - last packet at {stream.last_packet}")

        if len(self.streams) == 0:
            logging.info("All streams have stopped - putting display to sleep")
            self.leds.clearScreen()
            return

        # Sort the streams by priority, then currently active. This way the current stream stays active, unless a higher priority one joins
        self.streams = sorted(self.streams, key=lambda x: (x.priority, x.is_active), reverse=True)
        self.__set_active_index(active_index=0)
        logging.debug(f"__sync_clients() => Streams: {self.streams}")

    def __process_buffers(self) -> None:
        for stream in self.streams:
            for frame in stream.buffer.copy():
                if type(frame) is ImageFrame and stream.is_active:
                    # Take received packet and format for LED panel
                    ledframe = LedFrame(frame.height, frame.width)
                    ledframe.fill_from_bytearray(frame.pixels)
                    self.leds.displayFrame(ledframe)
                elif type(frame) is CommandFrame:
                    if frame.command == Commands.SetBrightness:
                        logging.info(f"[Stream {stream.client}] Setting brightness to {frame.value}")
                        self.leds.setBrightness(frame.value)
                    elif frame.command == Commands.SetPriority:
                        logging.info(f"[Stream {stream.client}] Setting priority to {frame.value}")
                        stream.priority = frame.value
                    else:
                        logging.warning(f"[Stream {stream.client}] Unkown Command received ({frame.command:x})")
                else:
                    logging.debug(f"[Stream {stream.client}] Ignoring ImageFrame from inactive stream")
                stream.buffer.pop(0)

    def handle_packet(self, network_frame) -> None:
        try:
            self.__ingest_frame(network_frame)
            self.__sync_clients()
            logging.debug(f"{len(self.streams)} streams - {self.streams}")
            self.__process_buffers()
        except FrameException as e:
            logging.error("Error while processing: %s" % e)

    def run(self) -> None:
        self.server.run(handler=self.handle_packet, service_actions=self.__sync_clients)
