"""
Unit tests for :mod:`jwt_proxy.http_base`.
"""

import unittest
from datetime import timedelta

from jwt_proxy.http_base import ProxyBaseHTTPRequestHandler


class TestRequestHandler(unittest.TestCase):
    """
    Tests for :class:`ProxyBaseHTTPRequestHandler`.
    """

    def test_format_time_duration(self):
        cases = {
            43.0: "43 seconds",
            43.7: "43 seconds",
            timedelta(minutes=14, seconds=36).total_seconds(): "14 minutes, 36 seconds",
            timedelta(minutes=59, seconds=59).total_seconds(): "59 minutes, 59 seconds",
            timedelta(hours=1).total_seconds(): "1 hours, 0 minutes, 0 seconds",
            timedelta(
                days=1, hours=2, minutes=38, seconds=12
            ).total_seconds(): "26 hours, 38 minutes, 12 seconds",
        }
        for duration, expected in sorted(cases.items()):
            self.assertEqual(expected, ProxyBaseHTTPRequestHandler.format_time_duration(duration))
