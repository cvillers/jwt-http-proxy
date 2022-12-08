.PHONY: build run stop test

PYTHON?=python
HTTP_PORT?=9100

all: run

build: *.py jwt_proxy/*.py
	docker compose build

run: build
	PROXY_HTTP_PORT=${HTTP_PORT} docker compose up -d

down:
	docker compose down

test:
	$(PYTHON) -m unittest discover
