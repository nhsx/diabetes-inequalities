#!/usr/bin/env python


import os
import logging

logger = logging.getLogger(__name__)

def _createCache(dir: str = '.'):
    path = f'{dir}/.esneft-cache'
    logger.info(f'Caching files to {path}')
    os.makedirs(path, exist_ok=True)
    return path


def setVerbosity(
        level=logging.INFO, handler=logging.StreamHandler(),
        format='%(name)s - %(levelname)s - %(message)s'):
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    esneft_logger = logging.getLogger('esneft_tools')
    esneft_logger.setLevel(level)
    esneft_logger.addHandler(handler)
