# HTTP JWT Proxy

This repository implements an HTTP reverse proxy which adds a JWT token to request headers.

Tested on Python 3.10, expected to work on Python 3.8+.

## Deployment and Usage

The servers run in Docker. The `Dockerfile` builds an image which is used to run both, and
the `docker-compose.yml` uses that image to run both services. The `Makefile` wraps the necessary commands.

### Usage

Start the servers with this command, which will build the images first. You can optionally override the proxy's
HTTP port with the HTTP_PORT variable.

```bash
$ make run HTTP_PORT=8888
```

Then, generate a POST body if desired, and send requests to the proxy server, which listens on port 9100 by default.
The JWT token in the below example has been omitted for brevity.

```bash
$ cat /tmp/data.txt
request body
$ curl -X POST -i --data-binary @/tmp/data.txt http://localhost:9100
HTTP/1.0 200 OK
Server: EchoServer Python/3.10.8
Date: Wed, 07 Dec 2022 02:40:24 GMT
Content-type: text/plain; charset=utf-8
Content-Length: 587

Path: /
Headers:
    Accept-Encoding: identity
    Host: localhost:9100
    User-Agent: curl/7.74.0
    Accept: */*
    Content-Length: 12
    Content-Type: application/x-www-form-urlencoded
    X-My-Jwt: [omitted for brevity]
    Connection: close
Body (12 bytes):
request body
```

### Status

Issue a GET to either server on the `/status` endpoint to receive some statistics about the current instance:

```bash
$ curl http://localhost:9100/status
JWTProxyServer up 38 seconds (since Thu, 08 Dec 2022 06:22:51 GMT)
7 requests processed

$ curl http://localhost:9200/status
EchoServer up 57 seconds (since Thu, 08 Dec 2022 06:22:51 GMT)
7 requests processed
```

### Environment variables

The servers can be configured with variables:

* `PROXY_HTTP_PORT`: The port where the proxy server listens. Also overridable in the Makefile as `HTTP_PORT`.
* `UPSTREAM_SERVER`: The server (`host[:port]` or `http[s]://host`) where the proxy sends upstream requests. Sub-paths are not supported.
* `JWT_SIGNING_SECRET`: The secret used for signing JWT tokens.
* `ECHO_HTTP_PORT`: The port where the echo server listens.

They can be overridden when bringing up the containers:

```bash
make run HTTP_PORT=8888 ECHO_HTTP_PORT=12345
```

## Components

### Proxy server
A reverse-proxy server which receives POST requests, appends a header containing a JWT token with the current username
and date, and forwards the request to a configurable upstream server.

### Echo server

A simple server for demonstrating the functionality of the proxy server, which logs information about the request and
echoes it back to the client.

## Development

This project has no external dependencies. The _black_ and _isort_ formatters are pinned in `requirements-dev.txt`
and configured in `pyproject.toml`.

### Local invocation

The servers can be run directly via entry point scripts:

```bash
./proxy_server.py
./echo_server.py
```

### Running tests

Use the Makefile; the Python interpreter can be overridden if necessary:

```bash
make test PYTHON=python3.10
```
