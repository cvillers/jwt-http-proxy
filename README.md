# HTTP JWT Proxy

This repository implements an HTTP proxy which adds a JWT token to request headers.

Dependencies:

* Python 3.10 (expected to work on 3.8+, not tested)
* [Poetry](https://python-poetry.org/) for venv management

## Deployment and Usage

The servers run in Docker. The `Dockerfile` builds an image which is used to run both, and
the `docker-compose.yml` uses that image to run both services.

### Usage

Run:

```bash
docker-compose up
```

### Environment variables

The servers can be configured with variables:

* `ECHO_HTTP_PORT`: The port where the echo server listens.

They can be overridden when bringing up the containers:

```bash
ECHO_HTTP_PORT=12345 docker-compose up
```

## Components

### Echo server

A simple server which logs information about the request and also echoes it back to the client.
This can be used to observe the operation of the proxy.

## Development

This project uses [Poetry](https://python-poetry.org/) for managing virtualenvs.

### Local invocation

The server entry points can be run directly:

```bash
poetry run python bin/echo_server.py
```

### Running tests

Use Poetry:

```bash
poetry run python -m unittest
```