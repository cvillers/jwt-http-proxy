# Entry point for the proxy server.

import os

from jwt_proxy.http_base import run_server
from jwt_proxy.logger import init_logging
from jwt_proxy.proxy_server import ProxyRequestHandler

init_logging()
run_server(ProxyRequestHandler, int(os.environ.get("PROXY_HTTP_PORT", 9100)))
