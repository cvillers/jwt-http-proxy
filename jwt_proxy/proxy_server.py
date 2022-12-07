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
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from jwt_proxy.http_base import ProxyBaseHTTPRequestHandler
from jwt_proxy.jwt import encode_jwt_hs512


class ProxyRequestHandler(ProxyBaseHTTPRequestHandler):
    """
    An HTTP server which adds a signed JWT header to POST requests.
    """

    server_version = "JWTProxyServer"

    JWT_TOKEN_HEADER = "x-my-jwt"

    def do_POST(self):
        self.record_request()
        self.logger.info("Got POST request for %s", self.path)

        # Read headers
        headers = OrderedDict()
        for name, value in self.headers.items():
            headers[name] = value

        # Input validation
        length = headers.get("Content-Length")
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
        upstream_url = self.build_upstream_url(self.path)
        headers[self.JWT_TOKEN_HEADER] = token
        upstream_request = Request(
            method="POST",
            url=upstream_url,
            data=req_body,
            headers=headers,
        )

        # Read the upstream response
        resp_status = HTTPStatus.OK
        resp_headers = []
        try:
            response: HTTPResponse = urlopen(upstream_request)

            resp_length = None
            resp_headers.extend(response.getheaders())
            for name, value in resp_headers:
                if name.lower() == "content-length":
                    resp_length = int(value)

            if resp_length is None:
                self.logger.error("Missing Content-Length header in upstream response!")
                self.send_error(HTTPStatus.BAD_GATEWAY, "missing length in upstream response")
                return
            resp_body = response.read(resp_length)
        except HTTPError as e:
            self.logger.error(
                "Error while submitting request to upstream %s", upstream_url, exc_info=e
            )
            resp_status = HTTPStatus.BAD_GATEWAY
            resp_body = f"{upstream_url} - {e.status} {e.reason}".encode("utf-8")
            resp_headers.append(("Content-type", "text/plain; charset=utf-8"))
            resp_headers.append(("Content-Length", str(len(resp_body))))

        # Build and send the response to the client
        self.send_proxy_response(resp_status)
        for name, value in resp_headers:
            self.send_header(name, value)
        self.end_headers()

        self.wfile.write(resp_body)
        self.wfile.flush()

    def send_proxy_response(self, code, message=None):
        """
        Variant of :meth:`BaseHTTPRequestHandler.send_response` which does not send
        ``Server`` or ``Date`` headers, so that the upstream headers are preserved.
        """
        self.log_request(code)
        self.send_response_only(code, message)

    @staticmethod
    def build_upstream_url(path: str) -> str:
        """
        Build the translated upstream URL.

        :param path: The URL path.
        :return: The complete new URL.
        """
        upstream = os.getenv("UPSTREAM_SERVER")
        if upstream is None:
            raise ValueError(
                "Could not get upstream server address from environment variable UPSTREAM_SERVER"
            )

        if "://" in upstream:
            scheme, netloc, _, params, query, fragment = urlparse(upstream)
        else:
            scheme = "http"
            netloc = upstream
            params = ""
            query = ""
            fragment = ""

        return urlunparse([scheme, netloc, path, params, query, fragment])
