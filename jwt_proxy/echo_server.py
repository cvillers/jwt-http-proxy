"""
Implements an HTTP server which logs all incoming requests and echoes information back to the client.
"""
import os
from http import HTTPStatus

from jwt_proxy.http_base import ProxyBaseHTTPRequestHandler, run_server
from jwt_proxy.logger import init_logging


class EchoRequestHandler(ProxyBaseHTTPRequestHandler):
    """
    A request handler which echoes information back to the client.
    """

    server_version = "EchoServer"

    def do_POST(self):
        self.logger.info("Got POST request for %s", self.path)

        # resp_lines is a list of messages to send back to the client
        resp_lines = ["Path: " + self.path, "Headers:"]
        # Log for debugging purposes, and also include in the echo response
        for k, v in sorted(dict(self.headers).items()):
            self.logger.info("    %s: %s", k, v)
            resp_lines.append(f"    {k}: {v}")

        # Basic validation
        length = self.headers.get("Content-Length")
        if length is None:
            self.logger.error("Missing Content-Length header!")
            self.send_error(HTTPStatus.BAD_REQUEST, "missing length")

        req_content = self.rfile.read(int(length))
        self.logger.info("Got %d bytes in POST body: %r", len(req_content), req_content)

        # Build and send the response
        resp_lines.append(f"Body ({length} bytes):")

        resp_message = "\n".join(resp_lines).encode("utf-8") + b"\n" + req_content

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(resp_message)))
        self.end_headers()

        self.wfile.write(resp_message)
        self.wfile.flush()
