#!/usr/bin/env python
# Entry point for the echo server.

import os

from jwt_proxy.echo_server import EchoRequestHandler
from jwt_proxy.http_base import run_server
from jwt_proxy.logger import init_logging

init_logging()
run_server(EchoRequestHandler, int(os.environ.get("ECHO_HTTP_PORT", 9200)))
