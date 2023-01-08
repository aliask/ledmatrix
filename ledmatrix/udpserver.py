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
        class PacketHandler(socketserver.BaseRequestHandler):
            def handle(pkself):
                data = pkself.request.recv(10240)
                if not data:
                    return

                addr = pkself.client_address
                try:
                    addr = socket.getnameinfo(pkself.client_address, 0)
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
