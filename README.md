# HTTP JWT Proxy

This repository implements an HTTP proxy which adds a JWT token to request headers.

## Components

### Echo server

A simple server which echoes back information about the request to the client.
This can be used to observe the operation of the proxy.

## Deployment

The servers run in Docker. The `Dockerfile` builds an image which is used to run both, and
the `docker-compose.yml` uses that image to run both services.

### Environment variables

The servers can be configured with variables:

* `ECHO_HTTP_PORT`: The port where the echo server listens.