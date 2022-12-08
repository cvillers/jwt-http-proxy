"""
Common utilities for unit tests.
"""
from http import HTTPStatus
from http.client import HTTPResponse, UnimplementedFileMode
from io import BytesIO
from typing import Callable, Dict, List, Optional, Union
from urllib.request import Request


class FakeSocket:
    """
    A mock socket which uses in-memory buffers.

    Copied from the stdlib test suite (Lib/test/test_httplib.py).
    """

    def __init__(self, text, fileclass=BytesIO, host=None, port=None):
        if isinstance(text, str):
            text = text.encode("ascii")
        self.text = text
        self.fileclass = fileclass
        self.data = b""
        self.sendall_calls = 0
        self.file_closed = False
        self.host = host
        self.port = port

    def sendall(self, data):
        self.sendall_calls += 1
        self.data += data

    def makefile(self, mode, bufsize=None):
        if mode != "r" and mode != "rb":
            raise UnimplementedFileMode()
        # keep the file around so we can check how much was read from it
        self.file = self.fileclass(self.text)
        self.file.close = self.file_close  # nerf close ()
        return self.file

    def file_close(self):
        self.file_closed = True

    def close(self):
        pass

    def setsockopt(self, level, optname, value):
        pass


def create_http_response(
    status: HTTPStatus,
    headers: Optional[Dict[str, str]] = None,
    content: Optional[bytes] = None,
) -> HTTPResponse:
    """
    Create an HTTP response.

    :param status: The status code.
    :param headers: The headers.
    :param content: The body content (optional).
    :return: The response.
    """

    lines = [f"HTTP 1.0 {status.value} {status.phrase}"]

    if headers is None:
        headers = {}
    if content is None:
        content = b""
    headers["Content-Length"] = str(len(content))
    for k, v in headers.items():
        lines.append(f"{k}: {v}")

    enc_headers = "\r\n".join(lines).encode("ascii")
    resp = HTTPResponse(FakeSocket(enc_headers + b"\r\n\r\n" + content))
    resp.chunked = False
    resp.headers = headers
    resp.length = len(content)
    return resp


class URLOpenPatch:
    def __init__(self):
        self.requests: List = []
        self.handlers: Dict[str, Callable[[Request], ...]] = {}

    def clean(self) -> None:
        """
        Clean up this patch instance.
        """
        self.requests.clear()
        self.handlers.clear()

    def invoke(self, url: Union[str, Request], data=None, *args, **kwargs) -> HTTPResponse:
        """
        Mock for :func:`urllib.request.urlopen`.

        :param url: The URL or request.
        :param data: The data.
        :param args: Unused arguments.
        :param kwargs: Unused arguments.
        :return: The response.
        """
        if isinstance(url, str):
            url = Request(url, data)
        self.requests.append(url)
        if url.full_url in self.handlers:
            return self.handlers[url.full_url](url)
        else:
            raise Exception(f"No handler function defined for URL {url.full_url}")

    def add_handler(self, url: str, function: Callable[[Request], HTTPResponse]):
        """
        Add a handlers function for a URL.

        :param url: The URL.
        :param function: The callable, which accepts a :class:`Request` and return an :class:`HTTPResponse`.
                         It should raise exceptions for invalid requests if that is the subject of the unit test,
                         otherwise it can return the desired HTTP status.
        """
        self.handlers[url] = function


urlopen_patch = URLOpenPatch()


def urlopen_patch_invoke(url, data=None, *args, **kwargs) -> HTTPResponse:
    """
    Mock for :func:`urllib.request.urlopen` which records requests and can
    return specified responses.
    """
    return urlopen_patch.invoke(url, data, *args, **kwargs)
