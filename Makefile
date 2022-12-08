.PHONY: build run stop test

HTTP_PORT?=9100

all: run

build: bin/*.py jwt_proxy/*.py
	docker compose build

run: build
	PROXY_HTTP_PORT=${HTTP_PORT} docker compose up -d

down:
	docker compose down

test:
	poetry run python -m unittest discover
