#!/usr/bin/env python

import os
import hashlib
import zipfile
import logging
import tempfile
import numpy as np
import pandas as pd
import urllib.request
from pathlib import Path


logger = logging.getLogger(__name__)


class getData():

    def __init__(self, cache: str = './.data-cache'):
        self.cache = cache
        self.host = ('https://raw.githubusercontent.com/'
                     'StephenRicher/nhsx-internship/main/data/')
        self.options = ({
            'LSOA': ['lsoa-name.json', 'postcode-lsoa.json'],
            'IMD': ['imd-statistics.json'],
            'Population': ['population-lsoa.json'],
            'GP': ['gp-registrations.json']
        })
        self.observedHashes = {}
        os.makedirs(self.cache , exist_ok=True)
        logger.info(f'Retrieved files will be cached to {self.cache}')


    @property
    def expectedHashes(self):
        return ({
            'lsoa-name.json': '2aac2ea909d2a53da0d64c4ad4fa6c5777e444bf725020217ed2b4c18a8a059f',
            'postcode-lsoa.json': 'eec8f006b1b1f3e6438bc9a3ac96be6bc316015c5321615a79417e295747d649',
            'imd-statistics.json': '82f654e30cb4691c7495779f52806391519267d68e8427e31ccdd90fb3901216',
            'population-lsoa.json': 'bec0349325a96da48634c6af3ebc8927fc1f79063f0056bebd420aceed13e533',
            'gp-registrations.json': '33c735683147f7597a59823ab116d182a220d906f266f9da75b6f6d1aaa220ca'
        })


    def fromHost(self, name: str):
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
                data = pd.read_json(path, typ='series').rename('index')
            if not os.path.exists(out):
                data.to_json(out)
            allData.append(data)
        return tuple(allData)


    def fromSource(self, name: str):
        """ Call function according to input """
        sourceMap = ({
            'LSOA': self._sourceLSOA,
            'IMD': self._sourceIMD,
            'Population': self._sourcePopulation,
            'GP': self._sourceGP
        })
        paths = self._getSourcePath(name)
        data = sourceMap[name]()
        for path in paths:
            sourceHash = self._checkHash(path)
            baseName = Path(path).name
            self.observedHashes[baseName] = sourceHash
            logger.info(f'Verifying hash of {baseName} ...')
            if sourceHash == self.expectedHashes[baseName]:
                logger.info('... source matches host file.')
            else:
                logger.error('... source does NOT match host file.')
        return data


    def _getSourcePath(self, name: str):
        paths = []
        for path in self.options[name]:
            paths.append(f'{self.cache}/{path}')
        return tuple(paths)


    def _checkHash(self, path: str, readSize: int = 4096):
        sha256Hash = hashlib.sha256()
        with open(path, 'rb') as f:
            data = f.read(readSize)
            while data:
                sha256Hash.update(data)
                data = f.read(readSize)
        return sha256Hash.hexdigest()


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

            paths = self._getSourcePath('LSOA')
            logger.info(f'Writing LSOA Code: Name map to {paths[0]}')
            lsoaNameMap = (lookup.set_index('LSOA11CD')['LSOA11NM']
                           .drop_duplicates())
            lsoaNameMap.to_json(paths[0])

            logger.info(f'Writing Postcode: LSOA map to {paths[1]}')
            postcodeLSOAmap = lookup.set_index('PCDS')['LSOA11CD']
            postcodeLSOAmap.to_json(paths[1])
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
        path, = self._getSourcePath('IMD')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/{name}')
            data = pd.read_csv(
                f'{tmp}/{name}', usecols=cols, names=dtype.keys(),
                dtype=dtype, skiprows=1, sep=',').set_index('LSOA11CD')
            data.to_json(path)
        return data


    def _sourcePopulation(self):
        name = 'SAP23DT2-mid2020-LSOA.xlsx'
        url = ('https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/'
               'populationandmigration/populationestimates/datasets/'
               'lowersuperoutputareamidyearpopulationestimates/mid2020sape23dt2/'
               'sape23dt2mid2020lsoasyoaestimatesunformatted.xlsx')
        headers = [(
            'Accept',
            'text/html,application/xhtml+xml,application/xml;'
            'q=0.9,image/avif,image/webp,*/*;q=0.8'
        )]
        logger.info(f'Downloading Population statistics from {url}')
        path, = self._getSourcePath('Population')
        with tempfile.TemporaryDirectory() as tmp:
            opener = urllib.request.build_opener()
            opener.addheaders = headers
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, f'{tmp}/{name}')
            pop = self._processPopulationSheet(f'{tmp}/{name}')
            pop_summary = (
                pop.groupby('LSOA11CD')
                .apply(self._summarisePopulation)
                .rename({0: 'medianAge', 1: 'Population'}, axis=1)
            )
            pop_summary.to_json(path)
        return pop_summary


    def _processPopulationSheet(self, path: str):
        dropCols = ([
            'LSOA Name', 'LA Code (2018 boundaries)',
            'LA name (2018 boundaries)', 'LA Code (2021 boundaries)',
            'LA name (2021 boundaries)', 'All Ages'
        ])
        pop = (pd.read_excel(path, sheet_name='Mid-2020 Persons', skiprows=4)
                 .rename({'LSOA Code': 'LSOA11CD', '90+': 90}, axis=1)
                 .drop(dropCols, axis=1)
                 .melt(id_vars='LSOA11CD', var_name='AgeYr',
                       value_name='Population')
        )
        return pop


    def _summarisePopulation(self, x):
        """ Get median Age and total populaiton by LSOA"""
        allAges = []
        for row in x.itertuples():
            allAges.extend([row.AgeYr] * row.Population)
        return pd.Series([np.median(allAges), x['Population'].sum()])


    def _sourceGP(self):
        url = ('https://files.digital.nhs.uk/AD/6A2BD9/'
               'gp-reg-pat-prac-lsoa-male-female-Jan-21.zip')
        logger.info(f'Downloading GP lookup from {url}')
        path, = self._getSourcePath('GP')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            dtype = ({
                'OrganisationCode': str,
                'LSOA11CD'        : str,
                'Patient'         : int,
            })
            cols = [2, 4, 6]
            gp_reg = pd.read_csv(
                f'{tmp}/gp-reg-pat-prac-lsoa-all.csv', skiprows=1,
                usecols=cols, dtype=dtype, names=dtype.keys())
            gp_reg.to_json(path)
        return gp_reg
