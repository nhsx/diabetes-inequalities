#!/usr/bin/env python

""" Functions used to download and process data for static GitHub hosting. """

import json
import logging
import zipfile
import tempfile
import pandas as pd
import urllib.request
from esneft_tools.utils import _createCache

logger = logging.getLogger(__name__)


def sourceLSOA(dir: str = '.') -> None:
    """ Retrieve LSOA -> Postcode Mapping, convert to JSON. """

    name = 'PCD_OA_LSOA_MSOA_LAD_FEB20_UK_LU.csv'
    url = ('https://www.arcgis.com/sharing/rest/content/items/'
           '6a46e14a6c2441e3ab08c7b277335558/data')

    logger.info(f'Downloading LSOA lookup from {url}')
    with tempfile.TemporaryDirectory() as tmp:
        urllib.request.urlretrieve(url, f'{tmp}/data.zip')
        with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
            zipRef.extractall(f'{tmp}/')

        dtype = ({
            'PCDS'    : str, # PCDS - Postcode
            'LSOA11CD': str, # LSOA Code (Census 2011)
            'LSOA11NM': str, # LSOA Name (Census 2011)
        })
        cols = [2, 7, 10]
        lookup = pd.read_csv(
            f'{tmp}/{name}', usecols=cols, names=dtype.keys(), dtype=dtype,
            skiprows=1, sep=',', encoding='latin-1')

        dir = _createCache(dir)

        path = f'{dir}/lsoa-name.json'
        logger.info(f'Writing LSOA Code: Name map to {path}')
        lsoaNameMap = lookup.set_index('LSOA11CD')['LSOA11NM'].to_dict()
        with open(path, 'w') as fh:
            json.dump(lsoaNameMap, fh)

        path = f'{dir}/postcode-lsoa.json'
        logger.info(f'Writing Postcode: LSOA map to {path}')
        postcodeLSOAmap = lookup.set_index('PCDS')['LSOA11CD'].to_dict()
        with open(path, 'w') as fh:
            json.dump(postcodeLSOAmap, fh)
