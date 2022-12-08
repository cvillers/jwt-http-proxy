"""
Unit tests for :mod:`jwt_proxy.proxy_server`.
"""

import os
import re
import unittest
from http import HTTPStatus
from io import BytesIO
from unittest import mock
from urllib.request import Request

from jwt_proxy.proxy_server import ProxyRequestHandler
from tests.common import create_http_response, urlopen_patch, urlopen_patch_invoke
from tests.test_jwt import SECRET


class UTProxyRequestHandler(ProxyRequestHandler):
    """
    Unittest-safe wrapper for :class:`ProxyRequestHandler` which provides the required constructor arguments.

    Based on the ``SocketlessRequestHandler`` in the stdlib test suite (Lib/test/test_httpservers.py).
    """

    def __init__(self):
        socket = mock.Mock()
        socket.makefile.return_value = BytesIO()
        server = mock.Mock()
        server.metrics_lock = mock.Mock()
        server.metrics_lock.__enter__ = mock.Mock(return_value=server.metrics_lock)
        server.metrics_lock.__exit__ = mock.Mock()
        super().__init__(socket, None, server)


class TestProxyServerRequestHandler(unittest.TestCase):
    """
    Tests for :class:`ProxyRequestHandler`. Based on ``BaseHTTPRequestHandlerTestCase``.
    """

    HTTPResponseMatch = re.compile(b"HTTP/1.[0-9]+ 200 OK")

    def setUp(self) -> None:
        self.handler = UTProxyRequestHandler()
        self.handler.client_address = ("127.0.0.1", 2345)
        self.urlopen_mock = mock.patch("jwt_proxy.proxy_server.urlopen", urlopen_patch_invoke)
        self.urlopen_mock.start()

    def tearDown(self) -> None:
        urlopen_patch.clean()
        self.urlopen_mock.stop()

    def send_typical_request(self, message):
        input = BytesIO(message)
        output = BytesIO()
        self.handler.rfile = input
        self.handler.wfile = output
        self.handler.handle_one_request()
        output.seek(0)
        return output.readlines()

    def verify_expected_headers(self, headers):
        for fieldName in b"Server: ", b"Date: ", b"Content-Type: ":
            self.assertEqual(sum(h.startswith(fieldName) for h in headers), 1)

    def verify_http_server_response(self, response):
        match = self.HTTPResponseMatch.search(response)
        self.assertIsNotNone(match)

    def test_build_upstream_url(self):
        # upstream url, path, expected result
        cases = [
            ("echo:9100", "/", "http://echo:9100/"),
            ("echo:9100", "/?a=b", "http://echo:9100/?a=b"),
            ("echo:9100", "/foo/bar?a=b", "http://echo:9100/foo/bar?a=b"),
            ("example.com", "/foo", "http://example.com/foo"),
            ("https://example.com", "/foo", "https://example.com/foo"),
        ]
        for server, path, expected in cases:
            os.environ["UPSTREAM_SERVER"] = server
            result = ProxyRequestHandler.build_upstream_url(path)
            self.assertEqual(result, expected)

    def test_handle_request(self):
        """
        Test for forwarding a response to the upstream server, with the JWT token appended.
        """

        def _validator(request: Request):
            # Check that it's structurally valid - we don't have a way to validate the actual signature
            token = request.get_header("X-my-jwt")
            self.assertIsNotNone(token, "x-my-jwt header is missing")
            self.assertRegex(
                token,
                rb"^[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+$",
                "x-my-jwt token does not follow JWT structure",
            )
            return create_http_response(HTTPStatus.OK, content=b"Example response")

        urlopen_patch.add_handler("http://test-upstream:1234/foo", _validator)

        os.environ["UPSTREAM_SERVER"] = "test-upstream:1234"
        os.environ["JWT_SIGNING_SECRET"] = SECRET.decode("ascii")

        req_body = b"Input body"
        req_lines = [
            "POST /foo HTTP/1.0".encode("ascii"),
            "Content-Type: application/x-www-form-urlencoded".encode("ascii"),
            f"Content-Length: {len(req_body)}".encode("ascii"),
        ]
        response = self.send_typical_request(b"\r\n".join(req_lines) + b"\r\n\r\n" + req_body)
        self.verify_http_server_response(response[0])
