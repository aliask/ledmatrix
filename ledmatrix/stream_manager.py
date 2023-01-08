from dataclasses import dataclass
import datetime
import logging
import threading
import time
from typing import List, Optional

from ledmatrix.ledframe import LedFrame
from ledmatrix.ledmatrix import LEDMatrix
from ledmatrix.tcpserver import TCPServer
from ledmatrix.udpserver import UDPServer
from ledmatrix.network_frame import (
    ImageFrame,
    CommandFrame,
    Command,
    NetworkFrame,
    FrameException,
)


DEFAULT_PRIORITY = 5


@dataclass
class Stream:
    client: str
    priority: int
    last_packet: datetime.datetime
    is_active: bool


class StreamManager:
    streams: List[Stream]
    tcp_server: TCPServer
    udp_server: UDPServer
    leds: LEDMatrix
    timeout: int
    frame_lock: threading.Lock

    def __init__(self, port: int, timeout: int, leds: LEDMatrix) -> None:
        self.streams = []
        self.leds = leds
        self.timeout = timeout
        self.frame_lock = threading.Lock()
        self.tcp_server = TCPServer(port=port)
        self.udp_server = UDPServer(port=port)

    def __ingest_frame(self, frame: NetworkFrame) -> None:
        """Process the incoming frame. If the frame belongs to the active stream, send it to the panels"""
        logging.debug(f"__ingest_frame(frame={frame})")

        if frame.source[0] not in [stream.client for stream in self.streams]:
            # Not found, create new stream for this client
            logging.info(
                f"[Stream {frame.source[0]}] Received frame from new source - {frame.source[0]}:{frame.source[1]}"
            )
            new_stream = Stream(
                client=frame.source[0],
                priority=DEFAULT_PRIORITY,
                last_packet=datetime.datetime.now(),
                is_active=False,
            )
            self.streams.append(new_stream)

        for stream in self.streams:
            if stream.client == frame.source[0]:
                stream.last_packet = datetime.datetime.now()
                if type(frame) is ImageFrame and stream.is_active:
                    # Take received packet and format for LED panel
                    ledframe = LedFrame(frame.height, frame.width)
                    ledframe.fill_from_bytes(frame.pixels)
                    self.leds.displayFrame(ledframe)
                elif type(frame) is CommandFrame:
                    if frame.command == Command.SetBrightness:
                        logging.info(f"[Stream {stream.client}] Setting brightness to {frame.value}")
                        self.leds.setBrightness(frame.value)
                    elif frame.command == Command.SetPriority:
                        logging.info(f"[Stream {stream.client}] Setting priority to {frame.value}")
                        stream.priority = frame.value
                    else:
                        logging.warning(f"[Stream {stream.client}] Unkown Command received (0x{frame.command:x})")
                else:
                    logging.debug(f"[Stream {stream.client}] Ignoring ImageFrame from inactive stream")

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

    def get_active_stream(self) -> Optional[Stream]:
        for stream in self.streams:
            if stream.is_active:
                return stream

    def sync_clients(self) -> None:
        """Removes stale clients, and sets the is_active property based on stream priority. If no streams remain, clear the LEDs"""
        # No clients to sync.
        if len(self.streams) == 0:
            return
        logging.debug("sync_clients()")

        cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=self.timeout)
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
        logging.debug(f"sync_clients() => Streams: {self.streams}")

    def handle_packet(self, network_frame: NetworkFrame) -> None:
        try:
            with self.frame_lock:
                self.__ingest_frame(network_frame)
        except FrameException as e:
            logging.error("Error while processing: %s" % e)

        self.sync_clients()
        logging.debug(f"{len(self.streams)} streams - {self.streams}")

    def run(self) -> None:
        self.tcp_server.run(handler=self.handle_packet)
        self.udp_server.run(handler=self.handle_packet)

        while True:
            self.sync_clients()
            time.sleep(1)
