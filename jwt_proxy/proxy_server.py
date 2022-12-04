"""
Implements an HTTP server which adds a signed JWT header to POST requests.
"""
import getpass
import os
from collections import OrderedDict
from datetime import date
from http import HTTPStatus
from http.client import HTTPResponse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from jwt_proxy.http_base import ProxyBaseHTTPRequestHandler
from jwt_proxy.jwt import encode_jwt_hs512


class ProxyRequestHandler(ProxyBaseHTTPRequestHandler):
    """
    An HTTP server which adds a signed JWT header to POST requests.
    """

    server_version = "JWTProxyServer"

    JWT_TOKEN_HEADER = "x-my-jwt"

    def do_CONNECT(self):
        """
        Handler for CONNECT requests which explicitly rejects the request.

        This is needed because the default :class:`BaseHTTPRequestHandler` sends a content response
        if a method is not implemented at all in this handler, which is not permitted for CONNECT per
        RFC 7231 section 4.3.6.
        """
        self.logger.info("Got CONNECT request for %s", self.path)
        self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
        self.end_headers()

    def do_POST(self):
        self.record_request()
        self.logger.info("Got POST request for %s", self.path)

        # Read headers
        client_headers = OrderedDict()
        for name, value in self.headers.items():
            client_headers[name] = value

        # Basic validation
        length = self.headers.get("Content-Length")
        if length is None:
            self.logger.error("Missing Content-Length header!")
            self.send_error(HTTPStatus.BAD_REQUEST, "missing length")
            return

        req_body = self.rfile.read(int(length))
        self.logger.info("Got %d bytes in POST body", len(req_body))

        # Generate the token
        token_payload = dict(user=getpass.getuser(), date=date.today().isoformat())
        token = encode_jwt_hs512(token_payload, os.getenv("JWT_SIGNING_SECRET").encode("ascii"))

        # Send the upstream request
        client_headers[self.JWT_TOKEN_HEADER] = token
        upstream_request = Request(
            url=self.path, data=req_body, headers=client_headers, method="POST"
        )

        resp_status = HTTPStatus.OK
        resp_headers = []
        # TODO factor this out
        # TODO wrap entire function this and return a 500 on error (global error handler)
        try:
            response: HTTPResponse = urlopen(upstream_request)

            # Read the upstream response
            resp_length = None
            resp_headers.extend(response.getheaders())
            for name, value in resp_headers:
                if name.lower() == "content-length":
                    resp_length = int(value)

            if resp_length is None:
                self.logger.error("Missing Content-Length header in response!")
                self.send_error(HTTPStatus.BAD_GATEWAY, "missing length in response")
                return
            resp_body = response.read(resp_length)
        except HTTPError as e:
            self.logger.error(
                "Error while submitting request to upstream %s", self.path, exc_info=e
            )
            resp_status = HTTPStatus.BAD_GATEWAY
            resp_body = f"{self.path} - {e.status} {e.reason}".encode("utf-8")
            resp_headers.append(("Content-type", "text/plain; charset=utf-8"))
            resp_headers.append(("Content-Length", str(len(resp_body))))

        # Build and send the response
        self.send_response(resp_status)
        for name, value in resp_headers:
            self.send_header(name, value)
        self.end_headers()

        self.wfile.write(resp_body)
        self.wfile.flush()

    def send_response(self, code, message=None):
        """
        Override of :meth:`BaseHTTPRequestHandler.send_response` which does not send
        ``Server`` or ``Date`` headers, so that the upstream headers are preserved.
        """
        self.log_request(code)
        self.send_response_only(code, message)
