# Note that there is no "pip install" step because no external dependencies are used.
FROM python:3.10.8-slim

ENV APP_DIR=/app

RUN mkdir $APP_DIR
WORKDIR $APP_DIR

COPY bin/*.py $APP_DIR/
ADD jwt_proxy/ $APP_DIR/jwt_proxy/
