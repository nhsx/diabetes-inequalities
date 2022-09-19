#!/usr/bin/env python

""" Functions used to download and process data for static GitHub hosting. """

import logging
import zipfile
import tempfile
import pandas as pd
import urllib.request
from esneft_tools.utils import _createCache

logger = logging.getLogger(__name__)


def sourceIMD(dir_: str = '.'):
    """ Retrieve IMD statistics """
    dir_ = _createCache(dir_)
    name = 'imd-statistics.json'
    url = ('https://assets.publishing.service.gov.uk/government/uploads/system'
           '/uploads/attachment_data/file/845345/File_7_-_All_IoD2019_Scores__'
           'Ranks__Deciles_and_Population_Denominators_3.csv')
    logger.info(f'Downloading IMD statistics from {url}')
    dtype = ({
        'LSOA11CD'            : str,   # LSOA code (2011)
        'IMD'                 : float, # Index of Multiple Deprivation (IMD) Score
        'Income'              : float, # Income Score (rate)
        'Employment'          : float, # Employment Score (rate)
        'Education'           : float, # Education, Skills and Training Score
        'Health'              : float, # Health Deprivation and Disability Score
        'Crime'               : float, # Crime Score
        'Barriers (H&S)'      : float, # Barriers to Housing and Services Score
        'Environment'         : float, # Living Environment
        'IDACI'               : float, # Income Deprivation Affecting Children Index (IDACI) Score (rate)
        'IDAOPI'              : float, # Income Deprivation Affecting Older People (IDAOPI) Score (rate)
        'YouthSubDomain'      : float, # Children and Young People Sub-domain Score
        'AdultSkills'         : float, # Adult Skills Sub-domain Score
        'Barriers (Geo)'      : float, # Geographical Barriers Sub-domain Score
        'Barriers (Wider)'    : float, # Wider Barriers Sub-domain Score
        'IndoorsSubDomain'    : float, # Indoors Sub-domain Score
        'OutdoorSubDomain'    : float, # Outdoors Sub-domain Score
        'Population (Total)'  : int,   # Total population: mid 2015 (excluding prisoners)
        'Population (0-15)'   : int,   # Dependent Children aged 0-15: mid 2015 (excluding prisoners)
        'Population (16-59)'  : int,   # Population aged 16-59: mid 2015 (excluding prisoners)
        'Population (60+)'    : int,   # Older population aged 60 and over: mid 2015 (excluding prisoners)
        'Population (Working)': int,   # Working age population 18-59/64: for use with Employment Deprivation Domain (excluding prisoners)
    })
    cols = ([
        0, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31,
        34, 37, 40, 43, 46, 49, 52, 53, 54, 55, 56
    ])
    with tempfile.TemporaryDirectory() as tmp:
        urllib.request.urlretrieve(url, f'{tmp}/{name}')
        data = pd.read_csv(
            f'{tmp}/{name}', usecols=cols, names=dtype.keys(),
            dtype=dtype, skiprows=1, sep=',').set_index('LSOA11CD')
        data.to_json(f'{dir_}/{name}')
    return data
