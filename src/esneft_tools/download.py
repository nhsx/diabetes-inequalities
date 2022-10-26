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
import numpy as np
import pandas as pd
import urllib.request
from datetime import date


logger = logging.getLogger(__name__)


try:
    import osmnx as ox
    import networkx as nx
except ModuleNotFoundError:
    logger.error('OSMNX not found - some features are unavailable.')

try:
    from pyproj import Transformer
except ModuleNotFoundError:
    logger.error('pyproj not found - some features are unavailable.')

try:
    import geopandas
except ModuleNotFoundError:
    logger.error('geopandas not found - some features are unavailable.')


class getData():

    def __init__(self, cache: str = './.data-cache'):
        self.cache = cache
        self.host = ('https://raw.githubusercontent.com/'
                     'StephenRicher/nhsx-internship/main/data/')
        self.options = ({
            'postcodeLSOA': 'postcode-lsoa.parquet',
            'imdLSOA': 'imd-statistics.parquet',
            'populationLSOA': 'population-lsoa.parquet',
            'areaLSOA': 'land-area-lsoa.parquet',
            'gpRegistration': 'gp-registrations.parquet',
            'gpPractice': 'gp-practices.parquet',
            'gpStaff': 'gp-staff.parquet',
            'qofDM': 'qof-dm.parquet',
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
            'postcodeLSOA': '34bf96ff8f316c6f9dada1d52dc8032e52bed7717d73b5fda4fe1d491e4cdb66',
            'postcodeLatLong': '1a57720e30f3c7e0843b14e3c4e9a0f8f6dba43714b02dfebf1adacbe0063bd8',
            'imdLSOA': 'af86bf505d9174a65cc87eb9ad97b85b2b53bf481d0e75c7cf41aa5645622aa2',
            'populationLSOA': '42cae583caf558be7aa285c94141c9d3151e3b4b66a15499e4fbf2d114d6ae36',
            'areaLSOA': '7f97767f8142754b81a6c8a0722d3d104a89e1a4c72276eb1dc00e06ebbca3ff',
            'gpRegistration': '920beffa35cba1d2cdcd879603cd886c337d550961048f3c13e2ac8d6e4cf8c2',
            'gpPractice': '3584ac0f169747f6a7486983a593db825703f947d7e63af004936abd354c0e93',
            'gpStaff': 'ffacd0da1b8b5c04aa0a1d96587e561438c54d61d8616507af14c6b11bc7d29e',
            'qofDM': 'c4e76d342125acbcc852549b3571afac5fa0299ffb48274b6339158cc4ede3c2',
            'geoLSOA': '608783e31e588706ca3215768fa6df6f08e88e1a51101a82f5587e52c483399f'
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
                open_ = urllib.request.urlopen
            if path.endswith('.geojson'):
                with open_(path) as geofile:
                    if os.path.exists(out):
                        data = geofile.read()
                    else:
                        data = geofile.read().decode('utf-8')
                    data = json.loads(data)
                if not os.path.exists(out):
                    with open(out, 'w') as fh:
                        json.dump(data, fh)
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
                # Get largest connected to prevent no pathing
                data = ox.utils_graph.get_largest_component(data)
                # Convert node names to string to prevent integer overflow
                relabel = {node: str(node) for node in data.nodes}
                data = nx.relabel_nodes(data, relabel)
            return data


    def fromSource(self, name: str):
        """ Call function according to input """
        sourceMap = ({
            'postcodeLSOA': self._sourceLSOA,
            'imdLSOA': self._sourceIMD,
            'populationLSOA': self._sourcePopulation,
            'areaLSOA': self._sourceArea,
            'gpRegistration': self._sourceGPregistration,
            'gpPractice': self._sourceGPpractice,
            'gpStaff': self._sourceGPstaff,
            'qofDM': self._sourceQOF,
            'geoLSOA': self._sourceMap,
        })
        data = sourceMap[name]()
        return data


    def _getSourcePath(self, name: str):
        return f'{self.cache}/{self.options[name]}'


    def _getHash(self, files, readSize: int = 4096):
        sha256Hash = hashlib.sha256()
        for file in files:
            with open(file, 'rb') as f:
                data = f.read(readSize)
                while data:
                    sha256Hash.update(data)
                    data = f.read(readSize)
        hash = sha256Hash.hexdigest()
        return hash


    def _verifyHash(self, name, files: list, readSize: int = 4096):
        self.observedHashes[name] = self._getHash(files, readSize)
        logger.info(f'Verifying hash of {name} ...')
        if self.observedHashes[name] == self.expectedHashes[name]:
            logger.info('... hash verification successful.')
            return 0
        else:
            logger.error('... hash verfication failed.')
            return 1


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
            self._verifyHash('postcodeLSOA', [f'{tmp}/{name}'])
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
        if G is not None:
            # Get rows in ESNEFT with Lat Long
            valid = (postcodeLSOA['ESNEFT']
                     & postcodeLSOA[['Lat', 'Long']].notna().all(axis=1))
            postcodeLSOA.loc[valid, 'Node'] = (
                ox.distance.nearest_nodes(G,
                    postcodeLSOA.loc[valid, 'Long'],
                    postcodeLSOA.loc[valid, 'Lat']))
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
            self._verifyHash('postcodeLatLong', files)
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
            self._verifyHash('imdLSOA', [f'{tmp}/{name}'])
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
            self._verifyHash('populationLSOA', [f'{tmp}/{name}'])
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


    def _sourceArea(self):
        url = ('https://www.arcgis.com/sharing/rest/content/items/'
               '5a94044d113a4bd5bd895975d6612b05/data')
        logger.info(f'Downloading LSOA land area lookup from {url}')
        path = self._getSourcePath('areaLSOA')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            self._verifyHash('areaLSOA', [f'{tmp}/SAM_LSOA_DEC_2011_EW.xlsx'])
            areaLSOA = (
                pd.read_excel(f'{tmp}/SAM_LSOA_DEC_2011_EW.xlsx')
                .set_index('LSOA11CD')
                .rename({'AREALHECT': 'LandHectare'}, axis=1)['LandHectare']
                .to_frame()
            )
        areaLSOA.to_parquet(path)
        return areaLSOA


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
            self._verifyHash(
                'gpRegistration', [f'{tmp}/gp-reg-pat-prac-lsoa-all.csv'])
            gpRegistration = pd.read_csv(
                f'{tmp}/gp-reg-pat-prac-lsoa-all.csv', skiprows=1,
                usecols=cols, dtype=dtype, names=dtype.keys())
        gpRegistration.to_parquet(path)
        return gpRegistration


    def _sourceGPpractice(self):
        url = 'https://files.digital.nhs.uk/assets/ods/current/epraccur.zip'
        logger.info(f'Downloading GP practice lookup from {url}')
        path = self._getSourcePath('gpPractice')
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
            self._verifyHash('gpPractice', [f'{tmp}/epraccur.csv'])
            gpPractices = pd.read_csv(
                f'{tmp}/epraccur.csv', usecols=cols, names=dtype.keys(),
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
        gpPractices['OpenDate'] = (
            pd.to_datetime(gpPractices['OpenDate'], format="%Y/%m/%d"))
        gpPractices['CloseDate'] = (
            pd.to_datetime(gpPractices['CloseDate'], format="%Y/%m/%d"))

        gpPractices['Status'] = gpPractices['Status'].replace(statusMap)
        gpPractices['PrescribingSetting'] = (
            gpPractices['PrescribingSetting'].replace(prescribingSetting))
        gpPractices = gpPractices.set_index('OrganisationCode')
        logger.info(f'Writing GP practice lookup to {path}')
        gpPractices.to_parquet(path)
        return gpPractices


    def _summariseStaff(self, x):
        """ Compute aggregate staff stats per practice """
        active = x['Left'].isna().any()
        start = pd.Timestamp(x['Joined'].min())
        end = pd.Timestamp(date.today()) if active else x['Left'].max()
        totalYears = ((end - start).days / 365.25)

        currentStaff = x['Current'].sum()
        leftStaff = (x['Left'] < end).sum()

        meanStaff = (x['Left'] - x['Joined']).dt.days.sum() / (end - start).days
        turnOver = ((leftStaff / meanStaff) / totalYears) * 100

        return pd.Series([currentStaff, leftStaff, meanStaff, turnOver])


    def _sourceGPstaff(self):
        url = 'https://files.digital.nhs.uk/assets/ods/current/epracmem.zip'
        logger.info(f'Downloading GP staff lookup from {url}')
        path = self._getSourcePath('gpStaff')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.zip')
            with zipfile.ZipFile(f'{tmp}/data.zip', 'r') as zipRef:
                zipRef.extractall(f'{tmp}/')
            dtype = ({
                'PractionerCode'  : str,
                'OrganisationCode': str,
                'Joined'          : str,
                'Left'            : str,
            })
            cols = [0, 1, 3, 4]
            self._verifyHash('gpStaff', [f'{tmp}/epracmem.csv'])
            gpStaff = pd.read_csv(
                f'{tmp}/epracmem.csv', usecols=cols,
                names=dtype.keys(), dtype=dtype, sep=',')
        gpStaff['Joined'] = pd.to_datetime(gpStaff['Joined'], format="%Y/%m/%d")
        gpStaff['Left'] = pd.to_datetime(gpStaff['Left'], format="%Y/%m/%d")
        gpStaff['Current'] = gpStaff['Left'].isna()
        gpStaff['Left'] = gpStaff['Left'].apply(
            lambda x: pd.to_datetime(date.today()) if pd.isnull(x) else x)
        names = ({
            0: 'currentStaff',
            1: 'departedStaff',
            2: 'meanStaff',
            3: 'annualStaffTurnover'
        })
        gpStaff = (
            gpStaff.groupby('OrganisationCode').apply(self._summariseStaff)
            .rename(names, axis=1))
        logger.info(f'Writing GP staff stats to {path}')
        gpStaff.to_parquet(path)
        return gpStaff


    def _sourceQOF(self):
        url = ('https://files.digital.nhs.uk/8A/57C8D5/'
               'qof-2122-prev-ach-pca-hd-prac.xlsx')
        logger.info(f'Downloading QOF 2020/2021 DM data from {url}')
        path = self._getSourcePath('qofDM')
        with tempfile.TemporaryDirectory() as tmp:
            urllib.request.urlretrieve(url, f'{tmp}/data.xlsx')
            names = ({
                'OrganisationCode': str,
                'Registered': int,
                'Diabetes': int,
                'QOF-DM': float,
                'DM019-num': int,
                'DM019-den': int,
                'DM020-num': int,
                'DM020-den': int,
            })
            cols = [5, 10, 12, 17, 54, 59, 62, 67]
            self._verifyHash('qofDM', [f'{tmp}/data.xlsx'])
            qofDM = pd.read_excel(
                f'{tmp}/data.xlsx', names=names.keys(), dtype=names,
                usecols=cols, skiprows=11, nrows=6470,
                sheet_name='DM').set_index('OrganisationCode')
        qofDM['DM-prevalance'] = qofDM['Diabetes'] / qofDM['Registered']
        qofDM['DM019-BP'] = qofDM['DM019-num'] / qofDM['DM019-den']
        qofDM['DM020-HbA1c'] = qofDM['DM020-num'] / qofDM['DM020-den']
        qofDM = qofDM.drop(
            ['Registered', 'Diabetes', 'DM019-num',
             'DM019-den', 'DM020-num', 'DM020-den'], axis=1)
        logger.info(f'Writing QOF data to {path}')
        qofDM.to_parquet(path)
        return qofDM


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
            self._verifyHash('geoLSOA', [f'{tmp}/infuse_lsoa_lyr_2011.shp'])
            geodf = geopandas.read_file(f'{tmp}/infuse_lsoa_lyr_2011.shp')
            geodf = geodf.loc[geodf['geo_code'].isin(esneftLSOA)]
            geodf = geodf.to_crs(epsg='4326')

            geodf.to_file(f'{tmp}/LSOA11-AOI-raw.geojson', driver='GeoJSON')
            with open(f'{tmp}/LSOA11-AOI-raw.geojson', encoding='utf-8') as geofile:
                geoLSOA11 = json.load(geofile)

            for i, feature in enumerate(geoLSOA11['features']):
                geoLSOA11['features'][i]['id'] = (
                    geoLSOA11['features'][i]['properties']['geo_code'])

            with open(path, 'w') as fh:
                json.dump(geoLSOA11, fh)
        return geoLSOA11
