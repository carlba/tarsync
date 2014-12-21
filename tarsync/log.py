import logging
from warp.logging import KwargsLoggingAdapter

dummy_dict = {}


def get_logger(name):
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(name)s:%(system)s:%(levelname)s:%(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    log = KwargsLoggingAdapter(logger, dummy_dict)
    return log
