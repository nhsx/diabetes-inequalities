#!/usr/bin/env python


import os
import logging

logger = logging.getLogger(__name__)


def setVerbosity(
        level=logging.INFO, handler=logging.StreamHandler(),
        format='%(name)s - %(levelname)s - %(message)s'):
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    esneft_logger = logging.getLogger('esneft_tools')
    esneft_logger.setLevel(level)
    esneft_logger.addHandler(handler)
