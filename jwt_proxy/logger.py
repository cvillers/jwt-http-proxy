"""
Logging subsystem helpers.
"""
import logging
from typing import Any, Callable, Union

_FORMAT = "%(asctime)s %(levelname)s [%(thread)5d] [%(name)s] %(message)s"


def get_logger(name: Union[str, Callable[[...], Any]]) -> logging.Logger:
    """
    Get a named logger.

    :param name: The name, or a callable which will have a name auto-generated.
    :return:
    """
    if callable(name):
        real_name = f"{name.__module__}.{name.__name__}"
    else:
        real_name = name
    return logging.getLogger(real_name)


def init_logging() -> None:
    """
    Initialize the logging system with standard configuration.
    """

    logging.basicConfig(format=_FORMAT, level=logging.DEBUG)
