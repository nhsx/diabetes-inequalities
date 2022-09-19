#!/usr/bin/env python

""" Retrieve copy of LSOA -> Postcode mappings """

# Source: https://www.arcgis.com/sharing/rest/content/items/6a46e14a6c2441e3ab08c7b277335558/data

import os
import zipfile
import logging
import tempfile
import pandas as pd
import urllib.request

logger = logging.getLogger(__name__)


class Data():

    def __init__(self, cache: str = './.data-cache'):
        self.cache = cache
        self.host = ('https://raw.githubusercontent.com/'
                     'StephenRicher/nhsx-internship/main/data/')
        self.options = ({
            'LSOA': ['lsoa-name.json', 'postcode-lsoa.json']
        })
        os.makedirs(self.cache , exist_ok=True)
        logger.info(f'Retrieved files will be cached to {self.cache}')


    def getData(self, name):
        allData = []
        for filename in self.options[name]:
            out = f'{self.cache}/{filename}'
            if os.path.exists(out):
                logger.info(f'Data already cached - loading from {out}')
                path = out
            else:
                path = f'{self.host}/{os.path.basename(out)}'
            try:
                data = pd.read_json(path)
            except ValueError:
                data = pd.read_json(path, typ='series')
            if not os.path.exists(out):
                data.to_json(out)
            allData.append(data)
        return tuple(allData)


    def sourceData(self, name):
        if name == 'LSOA':
            data = self._sourceLSOA()
        elif name == 'IMD':
            data = self._sourceIMD()
        return data


    def _sourceLSOA(self):
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

            path = f'{self.cache}/{self.options['LSOA'][0]}'
            logger.info(f'Writing LSOA Code: Name map to {path}')
            lsoaNameMap = (lookup.set_index('LSOA11CD')['LSOA11NM']
                           .drop_duplicates())
            lsoaNameMap.to_json(path)

            path = f'{self.cache}/{self.options['LSOA'][1]}'
            logger.info(f'Writing Postcode: LSOA map to {path}')
            postcodeLSOAmap = lookup.set_index('PCDS')['LSOA11CD']
            postcodeLSOAmap.to_json(path)

        return lsoaNameMap, postcodeLSOAmap


    def _sourceIMD(self):
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
            data.to_json(f'{self.cache}/{name}')
        return data


def getIMD(dir: str = '.') -> pd.DataFrame:
    dir = _createCache(dir)
    out = f'{dir}/imd-statistics.csv'
    if os.path.exists(out):
        logger.info(f'Lookup exists - loading from {out}.')
        imd = pd.read_csv(out)
    else:
        imd = pd.read_csv(f'{_url()}/imd-statistics.json')
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
