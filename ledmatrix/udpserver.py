#!/usr/bin/env python3
# Listener for Frame Data

import logging
import socket
import socketserver
import threading
from typing import Callable

from ledmatrix.network_frame import NetworkFrame, parse_frame


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass


class UDPServer:

    ALL_IFACES = "0.0.0.0"

    def __init__(self, port: int) -> None:
        self.port = port

    def run(self, handler: Callable[[NetworkFrame], None]):
        """Sets the request handling callback function, and starts the UDP server in a new thread"""
        class PacketHandler(socketserver.BaseRequestHandler):
            def handle(self):
                data = self.request[0]
                if not data:
                    return

                addr = self.client_address
                try:
                    addr = socket.getnameinfo(self.client_address, 0)
                except socket.gaierror:
                    logging.warn("Error during hostname lookup for %s" % addr[0])

                parsed = parse_frame(data)
                parsed.source = addr
                handler(parsed)

        logging.info(f"Starting UDP Server on {self.ALL_IFACES}:{self.port}")
        server = ThreadedUDPServer((self.ALL_IFACES, self.port), PacketHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
