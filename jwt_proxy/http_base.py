"""
Shared HTTP server implementation.
"""

import socket
import sys
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

    log.info("Listening on 0.0.0.0:%d", port)

    ThreadingHTTPServer.address_family = socket.AddressFamily.AF_INET
    with ThreadingHTTPServer(("0.0.0.0", port), handler_cls) as server:
        try:
            server.serve_forever()
        # TODO listen for signal sent by docker when terminating container
        except KeyboardInterrupt:
            log.info("Got ctrl-c, exiting")
            server.shutdown()
            sys.exit(0)
