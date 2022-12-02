"""
Utilities for encoding JWT.
"""

import base64
import hmac
import json
import secrets
import time
from typing import Dict, Optional, Union


def _base64_url(s: Union[str, bytes]) -> bytes:
    """
    Base64url-encode a string.

    :param s: The string.
    :return: The encoded form.
    """
    if isinstance(s, str):
        encoded = s.encode("utf-8")
    else:
        encoded = s
    return base64.urlsafe_b64encode(encoded).rstrip(b"=")


def encode_jwt_hs512(
    payload: Dict[str, str],
    secret: bytes,
    issued_at: Optional[int] = None,
    jwt_id: Optional[str] = None,
) -> bytes:
    """
    Create a signed JWT payload using the HS512 algorithm.

    :param payload: The payload dictionary.
    :param secret: The signing secret.
    :param issued_at: Timestamp (seconds since epoch) that the token was issued at. Pass None to use
                      the current timestamp.
    :param jwt_id: ID of the claim. Generally should not be overridden; only set this for unit tests.
    :return: The signed token.
    """
    header_msg = {
        "alg": "HS512",
        "typ": "jwt",
    }
    payload_msg = {
        "iat": issued_at or time.time(),
        "jti": jwt_id or secrets.token_hex(32),
        "payload": payload,
    }

    header_enc = _base64_url(json.dumps(header_msg, sort_keys=True))
    payload_enc = _base64_url(json.dumps(payload_msg, sort_keys=True))

    hm = hmac.new(secret, msg=header_enc + b"." + payload_enc, digestmod="sha512")

    sig = _base64_url(hm.digest())

    return header_enc + b"." + payload_enc + b"." + sig
