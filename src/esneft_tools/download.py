#!/usr/bin/env python

""" Retrieve copy of LSOA -> Postcode mappings """

# Source: https://www.arcgis.com/sharing/rest/content/items/6a46e14a6c2441e3ab08c7b277335558/data

import os
import logging
import pandas as pd
from esneft_tools.utils import _createCache

logger = logging.getLogger(__name__)


def _url():
    """ Base URL of data directory """
    return ('https://raw.githubusercontent.com/'
            'StephenRicher/nhsx-internship/main/data/')


def getLookup(dir: str = '.') -> pd.Series:
    dir = _createCache(dir)
    out = f'{dir}/postcode-lsoa-lookup.csv'
    if os.path.exists(out):
        logger.info(f'Lookup exists - loading from {out}.')
        pcd_lsoa = pd.read_csv(out)
    else:
        pcd_lsoa = (pd.read_json(f'{_url()}/postcode-lsoa.json', orient='index')
                    .reset_index()
                    .rename({'index': 'PCDS', 0: 'LSOA11CD'}, axis=1))
        pcd_lsoa.to_csv(out, index=False)
    return pcd_lsoa


def getIMD(dir: str = '.') -> pd.DataFrame:
    dir = _createCache(dir)
    out = f'{dir}/imd-statistics.csv'
    if os.path.exists(out):
        logger.info(f'Lookup exists - loading from {out}.')
        imd = pd.read_csv(out)
    else:
        imd = pd.read_csv(f'{_url()}/imd-statistics.csv')
        imd.to_csv(out, index=False)
    return imd


def getPopulation(dir: str = '.') -> tuple[pd.DataFrame, pd.DataFrame]:
    dir = _createCache(dir)
    data = {}
    for file in ['population-groups', 'population-medianAge']:
        out = f'{dir}/{file}.csv'
        if os.path.exists(out):
            logger.info(f'Lookup exists - loading from {out}.')
            pop = pd.read_csv(out)
        else:
            pop = pd.read_csv(f'{_url()}/{file}.csv')
            pop.to_csv(out, index=False)
        data[file] = pop
    return data['population-groups'], data['population-medianAge']
