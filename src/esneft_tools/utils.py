#!/usr/bin/env python


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


def formatP(p):
    """ Return formatted p for title """
    pformat = 'p '
    if p > 0.999:
        pformat += '> 0.999'
    elif p < 0.001:
        pformat += '< .001'
    else:
        pformat += '= ' + f'{p:.3f}'[1:]
    if p < 0.001:
        return pformat + ' ***'
    elif p < 0.01:
        return pformat + ' **'
    elif p < 0.05:
        return pformat + ' *'
    else:
        return pformat
