"""
Unit tests for :mod:`jwt_proxy.proxy_server`.
"""

import os
import unittest

from jwt_proxy.proxy_server import ProxyRequestHandler


class TestProxyServerRequestHandler(unittest.TestCase):
    """
    Tests for :class:`ProxyRequestHandler`.
    """

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
