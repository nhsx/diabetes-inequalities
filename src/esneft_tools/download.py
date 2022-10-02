#!/usr/bin/env python

import os
import sys
import json
import glob
import gzip
import hashlib
import zipfile
import logging
import tempfile
import pathlib
import geopandas
import osmnx as ox
import numpy as np
import pandas as pd
import urllib.request
from pathlib import Path
from pyproj import Transformer
from urllib.request import urlopen

logger = logging.getLogger(__name__)

try:
    import osmnx as ox
except ModuleNotFoundError:
    logger.error('OSMNX not found.')

class getData():

    def __init__(self, cache: str = './.data-cache'):
        self.cache = cache
        self.host = ('https://raw.githubusercontent.com/'
                     'StephenRicher/nhsx-internship/main/data/')
        self.options = ({
            'postcodeLSOA': 'postcode-lsoa.parquet',
            'imdLSOA': 'imd-statistics.parquet',
            'populationLSOA': 'population-lsoa.parquet',
            'gpRegistration': 'gp-registrations.parquet',
            'gpPractise': 'gp-practises.parquet',
            'esneftLSOA': 'lsoa-esneft.json',
            'geoLSOA': 'lsoa-map-esneft.geojson',
            'esneftOSM': 'esneft-highways.osm.gz'

        })
        self.observedHashes = {}
        self.osmnx = 'osmnx' in sys.modules
        os.makedirs(self.cache , exist_ok=True)
        logger.info(f'Retrieved files will be cached to {self.cache}')


    @property
    def expectedHashes(self):
        return ({
            'lsoa-name.parquet': '2aac2ea909d2a53da0d64c4ad4fa6c5777e444bf725020217ed2b4c18a8a059f',
            'postcode-lsoa.parquet': 'fed757144678f1de31bc5db40ec6fe67f4aea5058a720cac4b80ea6b28e4c49f',
            'imd-statistics.parquet': '4a20c6a394124205a767e2f420efb7604d7a9b45ce307cc3dd39fc6df7fc62ff',
            'population-lsoa.parquet': '4958ab685cd78ded47ecba494a9e1130ae7a2758bc8206cbeb6af3b5466f801a',
            'gp-registrations.parquet': 'b039285e697264315beb13d8922a605bdb30fe668d598d4ce9d2360f099831a8',
            'gp-practises.parquet': 'b5a600f47443a5cc20c1322ed90d879380c8c9f909886bb4ed7a20203395d8f4',
            'lsoa-map-esneft.geojson': '900f548cd72dbaff779af5fc333022f05e0ea42be162194576c6086ce695ba28'
        })


    def fromHost(self, name: str):
        if name == 'all':
            data = {}
            for name in self.options:
                data[name] = self.fromHost(name)
            return data
        elif (name == 'esneftOSM') and (not self.osmnx):
            logger.error(f'OSMNX not installed - skipping {name}.')
            return None
        else:
            out = f'{self.cache}/{self.options[name].removesuffix(".gz")}'
            if os.path.exists(out):
                logger.info(f'Data already cached - loading from {out}')
                path = out
                open_ = open
            else:
                path = f'{self.host}/{self.options[name]}'
                open_ = urlopen
            if path.endswith('.geojson'):
                with open_(path) as geofile:
                    data = json.load(geofile)
                if not os.path.exists(out):
                    with open(out, 'w') as fh:
                        json.dump(geoLSOA11, fh)
            elif path.endswith('.parquet'):
                data = pd.read_parquet(path)
                if not os.path.exists(out):
                    data.to_parquet(out)
            elif path.endswith('.json'):
                try:
                    data = pd.read_json(path)
                except ValueError:
                    data = pd.read_json(path, typ='series').rename('index')
                if not os.path.exists(out):
                    data.to_json(out)
            elif path.endswith('.osm.gz') or path.endswith('.osm'):
                if path.endswith('.osm.gz'):
                    with open_(path) as osm:
                        with gzip.open(osm, 'rt') as fh, open(out, 'w') as oh:
                            for line in fh:
                                oh.write(line)
                data = ox.graph.graph_from_xml(out, simplify=True)
            return data


    def fromSource(self, name: str):
        """ Call function according to input """
        sourceMap = ({
            'postcodeLSOA': self._sourceLSOA,
            'imdLSOA': self._sourceIMD,
            'populationLSOA': self._sourcePopulation,
            'gpRegistration': self._sourceGPregistration,
            'gpPractise': self._sourceGPpractise,
            'geoLSOA': self._sourceMap,
        })

        data = sourceMap[name]()
        path = self._getSourcePath(name)
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
        return f'{self.cache}/{self.options[name]}'


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
        path = self._getSourcePath('postcodeLSOA')
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
            postcodeLSOA = pd.read_csv(
                f'{tmp}/{name}', usecols=cols, names=dtype.keys(), dtype=dtype,
                skiprows=1, sep=',', encoding='latin-1')
        postcodeLSOA = postcodeLSOA.set_index('PCDS')
        esneftLSOA = self.fromHost('esneftLSOA')
        pcdGPS = self._sourcePostcodeLatLong()
        postcodeLSOA = (
            pd.concat([postcodeLSOA, pcdGPS], axis=1)
            .drop(['Eastings', 'Northings'], axis=1))
        postcodeLSOA['ESNEFT'] = postcodeLSOA['LSOA11CD'].isin(esneftLSOA)
        G = self.fromHost('esneftOSM')
        # Get rows in ESNEFT with Lat Long
        valid = (postcodeLSOA['ESNEFT']
                 & postcodeLSOA[['Lat', 'Long']].notna().all(axis=1))
        postcodeLSOA.loc[valid, 'Node'] = (
            ox.distance.nearest_nodes(G,
                postcodeLSOA.loc[valid, 'Long'],
                postcodeLSOA.loc[valid, 'Lat']))
        postcodeLSOA['Node'] = postcodeLSOA['Node'].fillna(-1).astype(int)
        logger.info(f'Writing Postcode: LSOA map to {path}')
        postcodeLSOA.to_parquet(path)
        return postcodeLSOA


    def _sourcePostcodeLatLong(self):
        url = ('https://api.os.uk/downloads/v1/products/CodePointOpen/'
               'downloads?area=GB&format=CSV&redirect')
        logger.info(f'Downloading Postcode Lat-Long lookup from {url}')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            files = glob.glob(f'{tmp}/Data/CSV/*csv')
            cols = ['PCDS', 'Eastings', 'Northings']
            pcdGPS = pd.concat([
                pd.read_csv(file, usecols=[0,2,3], names=cols, sep=',')
                for file in files]).set_index('PCDS')
        tf = Transformer.from_crs('epsg:27700', 'epsg:4326')
        pcdGPS['Lat'], pcdGPS['Long'] = zip(*pcdGPS.apply(
            lambda x: tf.transform(x['Eastings'], x['Northings']), axis=1))
        return pcdGPS


    def _sourceIMD(self):
        name = 'imd-statistics.parquet'
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
        path = self._getSourcePath('imdLSOA')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/{name}')
            imdLSOA = pd.read_csv(
                f'{tmp}/{name}', usecols=cols, names=dtype.keys(),
                dtype=dtype, skiprows=1, sep=',').set_index('LSOA11CD')
        imdLSOA.to_parquet(path)
        return imdLSOA


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
        path = self._getSourcePath('populationLSOA')
        with tempfile.TemporaryDirectory() as tmp:
            opener = urllib.request.build_opener()
            opener.addheaders = headers
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, f'{tmp}/{name}')
            populationLSOA = pd.concat([
                self._processPopulationSheet(f'{tmp}/{name}', 'Male'),
                self._processPopulationSheet(f'{tmp}/{name}', 'Female'),
            ])
        populationLSOA.to_parquet(path)
        return populationLSOA


    def _processPopulationSheet(self, path: str, sex: str):
        dropCols = ([
            'LSOA Name', 'LA Code (2018 boundaries)',
            'LA name (2018 boundaries)', 'LA Code (2021 boundaries)',
            'LA name (2021 boundaries)', 'All Ages'
        ])
        pop = (pd.read_excel(path, sheet_name=f'Mid-2020 {sex}s', skiprows=4)
                 .rename({'LSOA Code': 'LSOA11CD', '90+': 90}, axis=1)
                 .drop(dropCols, axis=1)
                 .melt(id_vars='LSOA11CD', var_name='Age',
                       value_name='Population')
        )
        pop['Sex'] = sex
        return pop


    def _sourceGPregistration(self):
        url = ('https://files.digital.nhs.uk/0E/59E17A/'
               'gp-reg-pat-prac-lsoa-male-female-July-2022.zip')
        logger.info(f'Downloading GP registration lookup from {url}')
        path = self._getSourcePath('gpRegistration')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            dtype = ({
                'OrganisationCode': str,
                'OranisationName' : str,
                'LSOA11CD'        : str,
                'Patient'         : int,
            })
            cols = [2, 3, 4, 6]
            gpRegistration = pd.read_csv(
                f'{tmp}/gp-reg-pat-prac-lsoa-all.csv', skiprows=1,
                usecols=cols, dtype=dtype, names=dtype.keys())
        gpRegistration.to_parquet(path)
        return gpRegistration


    def _sourceGPpractise(self):
        url = 'https://files.digital.nhs.uk/assets/ods/current/epraccur.zip'
        logger.info(f'Downloading GP practise lookup from {url}')
        path = self._getSourcePath('gpPractise')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            dtype = ({
                'OrganisationCode'  : str,
                'OrganisationName'  : str,
                'PCDS'              : str,
                'OpenDate'          : str,
                'CloseDate'         : str,
                'Status'            : str,
                'PrescribingSetting': int
            })
            cols = [0, 1, 9, 10, 11, 12, 25]
            gpPractises = pd.read_csv(
                f'{tmp}//epraccur.csv', usecols=cols, names=dtype.keys(),
                dtype=dtype, sep=',', encoding='latin-1')
        statusMap = ({
            'A': 'Active',
            'C': 'Closed',
            'D': 'Dormant',
            'P': 'Proposed'
        })
        prescribingSetting = ({
            0: 'Other', 1: 'WIC Practice', 2: 'OOH Practice',
            3: 'WIC + OOH Practice', 4: 'GP Practice', 8: 'Public Health Service',
            9: 'Community Health Service', 10: 'Hospital Service',
            11: 'Optometry Service', 12: 'Urgent & Emergency Care',
            13: 'Hospice', 14: 'Care Home / Nursing Home', 15: 'Border Force',
            16: 'Young Offender Institution', 17: 'Secure Training Centre',
            18: 'Secure Childrens Home', 19: 'Immigration Removal Centre',
            20: 'Court', 21: 'Police Custody', 22: 'Sexual Assault Referrral Centre',
            24: 'Other - Justice Estate', 25: 'Prison'
        })
        gpPractises['OpenDate'] = (
            pd.to_datetime(gpPractises['OpenDate'], format="%Y/%m/%d"))
        gpPractises['CloseDate'] = (
            pd.to_datetime(gpPractises['CloseDate'], format="%Y/%m/%d"))

        gpPractises['Status'] = gpPractises['Status'].replace(statusMap)
        gpPractises['PrescribingSetting'] = (
            gpPractises['PrescribingSetting'].replace(prescribingSetting))
        gpPractises = gpPractises.set_index('OrganisationCode')
        logger.info(f'Writing GP practise lookup to {path}')
        gpPractises.to_parquet(path)
        return gpPractises


    def _sourceMap(self):
        url = ('https://borders.ukdataservice.ac.uk/ukborders/easy_download/'
               'prebuilt/shape/infuse_lsoa_lyr_2011.zip')
        logger.info(f'Downloading LSOA Shapefile from {url}')
        path = self._getSourcePath('geoLSOA')
        esneftLSOA = self.fromHost('esneftLSOA')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            geodf = geopandas.read_file(f'{tmp}/infuse_lsoa_lyr_2011.shp')
            geodf = geodf.loc[geodf['geo_code'].isin(esneftLSOA)]
            geodf = geodf.to_crs(epsg='4326')

            geodf.to_file(f'{tmp}/LSOA11-AOI-raw.geojson', driver='GeoJSON')
            with open(f'{tmp}/LSOA11-AOI-raw.geojson') as geofile:
                geoLSOA11 = json.load(geofile)

            for i, feature in enumerate(geoLSOA11['features']):
                geoLSOA11['features'][i]['id'] = (
                    geoLSOA11['features'][i]['properties']['geo_code'])

            with open(path, 'w') as fh:
                json.dump(geoLSOA11, fh)
        return geoLSOA11
