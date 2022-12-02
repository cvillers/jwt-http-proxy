"""
Unit tests for :mod:`jwt_proxy.jwt`.
"""

import unittest

from jwt_proxy.jwt import encode_jwt_hs512

SECRET = b"be209f0400598c8c2e9fb4447d334c7e253e76b97e454f72bce0b137e617e64396bae53b22c52b7a203d4a83e012bab4f1061006bf4861bf279c33ac4aad745d"


class TestJWT(unittest.TestCase):
    def test_jwt_encode(self):
        payload = {
            "claim1": "foo",
            "claim2": "bar",
        }
        encoded = encode_jwt_hs512(
            payload,
            SECRET,
            1669947303,
            "307a54f14289be92516c9c25435d1dd706aa28eea680437e01f7fa4723469063",
        )
        self.assertEqual(
            encoded,
            b"eyJhbGciOiAiSFM1MTIiLCAidHlwIjogImp3dCJ9.eyJpYXQiOiAxNjY5OTQ3MzAzLCAianRpIjogIjMwN2E1NGYxNDI4OWJlOTI1MTZjOWMyNTQzNWQxZGQ3MDZhYTI4ZWVhNjgwNDM3ZTAxZjdmYTQ3MjM0NjkwNjMiLCAicGF5bG9hZCI6IHsiY2xhaW0xIjogImZvbyIsICJjbGFpbTIiOiAiYmFyIn19.434Zb6j3QTCJA4GKAKNggOIaI3yoyagOumwe-hA65UEoa_XduRJ1VwtGyKk8S1I42FMiOfvJvBqGR3N6WaL1iA",
        )
