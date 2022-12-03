"""
Shared HTTP server implementation.
"""

import signal
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jwt_proxy.logger import get_logger


class ProxyBaseHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Common HTTP request handler shared by both the proxy and the echo server.
    """

    @property
    def logger(self):
        # workaround for __init__ not being called
        if not hasattr(self, "__log"):
            self.__log = get_logger(type(self))
        return self.__log

    def log_error(self, format: str, *args) -> None:
        self.logger.error("[%s] %s", self.address_string(), format % args)

    def log_message(self, format: str, *args) -> None:
        self.logger.info("[%s] %s", self.address_string(), format % args)


def run_server(handler_cls, port: int):
    """
    Run an HTTP server.

    :param server_cls: The :class:`http.server.HTTPServer` class type.
    :param handler_cls: The :class:`BaseHTTPRequestHandler` class type.
    :param port: The port to listen on.
    """
    log = get_logger(run_server)

    log.info("Starting server on on 0.0.0.0:%d", port)

    ThreadingHTTPServer.address_family = socket.AddressFamily.AF_INET

    with ThreadingHTTPServer(("0.0.0.0", port), handler_cls) as server:
        # Run the server on another thread so that the main thread can handle the shutdown signal.
        # running will be set by the signal handler, and then the main thread will resume and
        # gracefully shut down.
        thread = threading.Thread(target=server.serve_forever, daemon=True, name="server-main")

        running = True

        def _handler(signum, frame):
            log.info("Got signal %d (%s), exiting", signum, signal.strsignal(signum))
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)

        thread.start()

        log.info("Started server")

        while running:
            time.sleep(0.01)

        log.info("Shutting down")
        server.shutdown()
        sys.exit(0)
