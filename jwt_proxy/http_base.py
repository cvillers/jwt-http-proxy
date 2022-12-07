"""
Shared HTTP server components.
"""

import signal
import socket
import sys
import threading
import time
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from math import floor
from typing import Union

from jwt_proxy.logger import get_logger

_REQUESTS_PROCESSED_METRIC_KEY = "requests_processed"


class ProxyHTTPServer(ThreadingHTTPServer):
    """
    Override of :class:`ThreadingHTTPServer` which stores global metrics that can be accessed
    by request handlers, because request handlers are instantiated freshly for each request.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.metrics_lock = threading.Lock()
        self.metrics = Counter(_REQUESTS_PROCESSED_METRIC_KEY=0)


class ProxyBaseHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Common HTTP request handler shared by both the proxy and the echo server.
    """

    def __init__(self, socket, client, server: ProxyHTTPServer):
        # Assign instance variables first because the parent constructor will call handler methods
        self._server = server
        self.logger = get_logger(type(self))
        super(BaseHTTPRequestHandler, self).__init__(socket, client, server)

    def record_request(self) -> None:
        """
        Add a metric that a request was processed.
        """
        with self._server.metrics_lock:
            self._server.metrics[_REQUESTS_PROCESSED_METRIC_KEY] += 1

    def do_GET(self):
        if self.path == "/status":
            status = HTTPStatus.NOT_FOUND
            response = b"Not Found"
        else:
            status = HTTPStatus.OK
            now = time.time()
            started = self.date_time_string(self._server.start_time)
            uptime = self.format_time_duration(now - self._server.start_time)

            response_lines = [f"{self.server_version} up {uptime} (since {started})"]
            with self._server.metrics_lock:
                response_lines.append(
                    f"{self._server.metrics[_REQUESTS_PROCESSED_METRIC_KEY]} requests processed"
                )
            response = "\n".join(response_lines).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        self.wfile.write(response)
        self.wfile.flush()

    @staticmethod
    def format_time_duration(duration_secs: Union[int, float]) -> str:
        """
        Describe the time as a duration.

        :param duration_secs: The duration as a number of seconds.
        :return: The duration.
        """
        parts = []
        seconds = floor(duration_secs % 60)
        minutes = floor((duration_secs % (60 * 60)) / 60)
        hours = floor(duration_secs / (60 * 60))

        if minutes < 1 and hours < 1:
            parts.append(f"{int(seconds)} seconds")
        elif minutes < 60 and hours < 1:
            parts.append(f"{int(minutes)} minutes")
            parts.append(f"{int(seconds)} seconds")
        else:
            parts.append(f"{int(hours)} hours")
            parts.append(f"{int(minutes)} minutes")
            parts.append(f"{int(seconds)} seconds")

        return ", ".join(parts)

    # Overrides of the base log functions, to funnel everything through the standard logger
    def log_error(self, format: str, *args) -> None:
        self.logger.error("[%s] %s", self.address_string(), format % args)

    def log_message(self, format: str, *args) -> None:
        self.logger.info("[%s] %s", self.address_string(), format % args)


def run_server(handler_cls, port: int):
    """
    Run an HTTP server.

    :param handler_cls: The :class:`BaseHTTPRequestHandler` class type.
    :param port: The port to listen on.
    """
    log = get_logger(run_server)

    log.info("Starting server on on 0.0.0.0:%d", port)

    ProxyHTTPServer.address_family = socket.AddressFamily.AF_INET

    with ProxyHTTPServer(("0.0.0.0", port), handler_cls) as server:
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
