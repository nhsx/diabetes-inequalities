#!/usr/bin/env python

import sys
import logging
import numpy as np
import pandas as pd
from collections import defaultdict


logger = logging.getLogger(__name__)


try:
    import osmnx as ox
    import networkx as nx
except ModuleNotFoundError:
    logger.error('OSMNX not found - some features are unavailable.')


def _weightedMean(x, cols, w='Patient'):
    """ Apply weighted mean on groupby object """
    return pd.Series(np.average(x[cols], weights=x[w], axis=0), cols)


def _parseIoDcols(imd: pd.DataFrame, iod_cols: list = None):
    if iod_cols is None:
        iod_cols = [col for col in imd.columns if col != 'LSOA11NM']
    elif isinstance(iod_cols, str):
        iod_cols = [iod_cols]
    elif not isinstance(iod_cols, list):
        logging.error('iod_cols must be a list or a single column string.')
        raise ValueError
    return iod_cols


def getGPsummary(gpRegistration, gpPractice, gpStaff,
                 postcodeLSOA, imdLSOA, esneftOSM,
                 qof, iod_cols: list = None, bins: int = 5,
                 quantile: bool = True, **kwargs):
    """ Compute mean IoD per GP practice weighted by patient population """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    summary = (pd
        .merge(gpRegistration, imdLSOA[iod_cols],
               left_on='LSOA11CD', right_index=True)
        .groupby(['OrganisationCode'])
        .apply(_weightedMean, iod_cols))
    summary['Patient'] = (
        gpRegistration.groupby('OrganisationCode')['Patient'].sum())
    summary = pd.concat([summary, qof, gpPractice, gpStaff], axis=1)
    summary = pd.merge(
        summary, postcodeLSOA[['Lat', 'Long']], left_on='PCDS',
        right_index=True, how='left')
    summary['patientPerGP'] = summary['Patient'] / summary['meanStaff']
    summary['ESNEFT'] = summary['PCDS'].isin(
        postcodeLSOA.loc[postcodeLSOA['ESNEFT']].index)
    cutter = pd.qcut if quantile else pd.cut
    name = 'q' if quantile else 'i'
    for col in iod_cols:
        summary[f'{col} ({name}{bins})'] = cutter(
            summary[col], bins, labels=list(range(bins, 0, -1)))
        summary[f'{col} ({name}{bins})'] = (
            summary[f'{col} ({name}{bins})'].astype(float).fillna(-1).astype(int))
    if (esneftOSM is not None) and ('osmnx' in sys.modules):
        valid = summary[['Lat', 'Long']].notna().all(axis=1)
        summary.loc[valid, 'Node'] = ox.distance.nearest_nodes(
            esneftOSM, summary.loc[valid, 'Long'], summary.loc[valid, 'Lat'])
    return summary


def getLSOAsummary(postcodeLSOA, imdLSOA, gpRegistration, populationLSOA,
                   ethnicityLSOA, areaLSOA, esneftLSOA, qof,
                   iod_cols: list = None, bins: int = 5,
                   quantile: bool = True, **kwargs):
    """ Return summary statistics per LSOA """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    maleProp = (
        populationLSOA.groupby('LSOA11CD')
        .apply(_getSexRatio).rename('MaleProp'))
    populationLSOA = (
        populationLSOA.groupby('LSOA11CD')
        .apply(_summarisePopulation)
        .rename({0: 'Age (median)', 1: 'Population'}, axis=1))
    # Get GP registration by LSOA
    gpRegistrationByLSOA = gpRegistration.groupby('LSOA11CD')['Patient'].sum()
    # Get number of GPs serving proportion of population
    gpDensity = (gpRegistration
        .groupby('LSOA11CD')['Patient']
        .apply(_getGPthreshold, 0.9)
        .rename('GPservices'))
    summary = pd.concat([
        imdLSOA['LSOA11NM'], populationLSOA, maleProp,
        ethnicityLSOA, areaLSOA, gpRegistrationByLSOA,
        gpDensity, imdLSOA[iod_cols]], axis=1)
    cutter = pd.qcut if quantile else pd.cut
    name = 'q' if quantile else 'i'
    for col in iod_cols:
        summary[f'{col} ({name}{bins})'] = cutter(
            summary[col], bins, labels=list(range(bins, 0, -1)))
        summary[f'{col} ({name}{bins})'] = (
            summary[f'{col} ({name}{bins})'].astype(float).fillna(-1).astype(int))
    diseases = [c for c in qof.columns if c.endswith('-prevalance')]
    for disease in diseases:
        logger.info(f'Processing {disease}.')
        summary[disease] = _getLSOAweightedMean(
            gpRegistration, qof, gp_col='OrganisationCode',
            score_col=disease, weight_col='Patient')
    summary['DM-QOF'] = _getLSOAweightedMean(
        gpRegistration, qof, gp_col='OrganisationCode',
        score_col='QOF-DM', weight_col='Patient')
    summary['DM-BP'] = _getLSOAweightedMean(
        gpRegistration, qof, gp_col='OrganisationCode',
        score_col='DM019-BP', weight_col='Patient')
    summary['DM-HbA1c'] = _getLSOAweightedMean(
        gpRegistration, qof, gp_col='OrganisationCode',
        score_col='DM020-HbA1c', weight_col='Patient')
    summary['Density'] = summary['Population'] / summary['LandHectare']
    summary['ESNEFT'] = summary.index.isin(esneftLSOA)
    # Only consider England data
    lsoa_england = imdLSOA.index
    summary = summary.loc[summary.index.isin(lsoa_england)].copy()
    return summary


def _getSexRatio(x):
    """ Get proportion of male residents """
    total = x['Population'].sum()
    male = x.loc[x['Sex'] != 'Male', 'Population'].sum()
    return male / total


def _getGPthreshold(x, threshold=0.9):
    cumprop = x.sort_values(ascending=False).cumsum() / x.sum()
    return (cumprop < threshold).sum() + 1


def _getLSOAweightedMean(gpRegistration, df, gp_col, score_col, weight_col):
    """ Compute LSOA prevalence by weighted mean across GP """
    gpTmp = pd.merge(
        gpRegistration, df,
        left_on=gp_col, right_index=True)
    gpTmp = gpTmp.loc[gpTmp[weight_col] > 0]
    prevalance = (
        gpTmp.groupby('LSOA11CD')
        .apply(lambda x: np.average(x[score_col], weights=x[weight_col])))
    return prevalance


def _summarisePopulation(x):
    """ Get median Age and total populaiton by LSOA"""
    allAges = []
    for row in x.itertuples():
        allAges.extend([row.Age] * row.Population)
    return pd.Series([np.median(allAges), x['Population'].sum()])


def _checkInBounds(x, bounds):
    return (
            bounds[0] <= x['Long'] <= bounds[2]
        and bounds[1] <= x['Lat'] <= bounds[3]
    )


def computeTravelDistance(G, locations, dist=20000):
    fullBounds = ox.graph_to_gdfs(G, edges=False).total_bounds
    inBounds = locations.apply(_checkInBounds, args=(fullBounds,), axis=1)
    locations = locations.loc[inBounds].copy()
    distances = defaultdict(lambda: (np.inf, None))
    # Retrieve dictionary of ref nodes mapping to site ID
    nodeSites = (locations.groupby('Node').apply(
        lambda x: tuple(x.index)).to_dict())
    checked = set()
    for i, refNode in enumerate(locations['Node'].unique()):
        subgraph = nx.ego_graph(G, refNode, radius=dist, distance='length')
        allShortest = nx.shortest_path_length(
            subgraph, refNode, weight='length', method='dijkstra')
        for node, distance in allShortest.items():
            if distance < distances[node][0]:
                distances[node] = (distance, nodeSites[refNode])
        checked.update(set(subgraph.nodes()))
    completion = len(checked) / len(G.nodes())
    unchecked = set(G.nodes()) - checked
    logger.info(
        f'{completion:.1%} complete, {len(unchecked)} nodes > {dist} away.')
    distances = pd.DataFrame.from_dict(
        distances, orient='index', columns=['Distance', 'SiteIDs'])
    return distances, unchecked


def prepTime(df, start, end=None, interval='1W', group=None, index=None):
    """ Standardise timeline events data by group """
    valid = [start] if end is None else [start, end]
    df = df.loc[df[valid].notna().all(axis=1)].copy()
    if group is None:
        df['group'] = ''
    else:
        df['group'] = df[group].fillna('Unknown')
    df['start'] = pd.to_datetime(df[start])
    if end is None:
        end = f'start+{interval}'
        df[end] = df['start'] + pd.Timedelta(1)
    df['start'] = df['start'].dt.to_period(interval).dt.start_time
    df['end'] = (
        pd.to_datetime(df[end]).dt.to_period(interval).dt.end_time
        + pd.Timedelta(1)
    )
    cols = ['group', 'start', 'end']
    if index is None:
        drop = False # Save the pandas index column
    else:
        drop = True
        cols.append(index)
    return df[cols].reset_index(drop=drop)


def summariseTime(df: pd.DataFrame, interval='1W', normByGroup: bool = False):
    """ Compute normalised event frequency within constant time interval """
    mergeFunc = lambda x: pd.date_range(x['start'], x['end'], freq=interval)
    df = pd.merge(
        df, df.apply(mergeFunc, axis=1).explode().rename('period'),
        left_index=True, right_index=True)

    df['period'] = df['period'].dt.to_period(interval)
    groups = ['group', 'period']
    df = df.groupby(groups).size().reset_index()

    df['start'] = df['period'].dt.start_time
    df['end'] = df['period'].dt.end_time + pd.Timedelta(1)

    if normByGroup:
        df['Freq.'] = df.groupby('group')[0].transform(lambda x: x / x.max())
        order = None
    else:
        df['Freq.'] = df[0] / df[0].max()
        order = df.groupby('group')['Freq.'].sum().sort_values().index
    return df.drop(['period', 0], axis=1)
