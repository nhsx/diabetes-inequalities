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
        iod_cols = imd.columns
    elif isinstance(iod_cols, str):
        iod_cols = [iod_cols]
    elif not isinstance(iod_cols, list):
        logging.error('iod_cols must be a list or a single column string.')
        raise ValueError
    return iod_cols


def getGPsummary(gpRegistration, gpPractice, gpStaff,
                 postcodeLSOA, imdLSOA, esneftOSM,
                 qofDM, iod_cols: list = None, **kwargs):
    """ Compute mean IoD per GP practice weighted by patient population """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    summary = (pd
        .merge(gpRegistration, imdLSOA[iod_cols],
               left_on='LSOA11CD', right_index=True)
        .groupby(['OrganisationCode'])
        .apply(_weightedMean, iod_cols))
    summary['Patient'] = (
        gpRegistration.groupby('OrganisationCode')['Patient'].sum())
    summary = pd.concat([summary, qofDM, gpPractice, gpStaff], axis=1)
    summary = pd.merge(
        summary, postcodeLSOA[['Lat', 'Long']], left_on='PCDS',
        right_index=True, how='left')
    summary['patientPerGP'] = summary['Patient'] / summary['meanStaff']
    summary['ESNEFT'] = summary['PCDS'].isin(
        postcodeLSOA.loc[postcodeLSOA['ESNEFT']].index)
    if (esneftOSM is not None) and ('osmnx' in sys.modules):
        valid = summary[['Lat', 'Long']].notna().all(axis=1)
        summary.loc[valid, 'Node'] = ox.distance.nearest_nodes(
            esneftOSM, summary.loc[valid, 'Long'], summary.loc[valid, 'Lat'])
    return summary


def getLSOAsummary(postcodeLSOA, imdLSOA, gpRegistration, populationLSOA,
                   areaLSOA, esneftLSOA, qofDM, iod_cols: list = None,
                   bins: int = 5, quantile: bool = True, **kwargs):
    """ Return summary statistics per LSOA """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    populationLSOA = (
        populationLSOA.groupby('LSOA11CD')
        .apply(_summarisePopulation)
        .rename({0: 'Age (median)', 1: 'Population'}, axis=1))
    # Get GP registration by LSOA
    gpRegistrationByLSOA = gpRegistration.groupby('LSOA11CD')['Patient'].sum()
    # Extract LSOA Name
    lsoaName = (
        postcodeLSOA.reset_index(drop=True)
        .set_index('LSOA11CD')['LSOA11NM'].drop_duplicates())
    summary = pd.concat([
        lsoaName, populationLSOA, areaLSOA,
        gpRegistrationByLSOA, imdLSOA[iod_cols]], axis=1)
    cutter = pd.qcut if quantile else pd.cut
    name = 'q' if quantile else 'i'
    for col in iod_cols:
        summary[f'{col} ({name}{bins})'] = cutter(
            summary[col], bins, labels=list(range(bins, 0, -1)))
    summary['DM-prevalance'] = _getLSOAprevalence(gpRegistration, qofDM)
    summary['Density'] = summary['Population'] / summary['LandHectare']
    summary['ESNEFT'] = summary.index.isin(esneftLSOA)
    return summary


def _getLSOAprevalence(gpRegistration, qofDM):
    """ Compute LSOA prevalence by weighted mean across GP """
    gpTmp = pd.merge(
        gpRegistration, qofDM,
        left_on='OrganisationCode', right_index=True)
    prevalance = (
        gpTmp.groupby('LSOA11CD')
        .apply(lambda x: np.average(x['DM-prevalance'], weights=x['Patient'])))
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


def computeTravelDistance(G, locations, step=500, maxQuant=0.95):
    fullBounds = ox.graph_to_gdfs(G, edges=False).total_bounds
    inBounds = locations.apply(_checkInBounds, args=(fullBounds,), axis=1)
    locations = locations.loc[inBounds].copy()
    distances = defaultdict(lambda: (np.inf, None))
    # Retrieve dictionary of ref nodes mapping to site ID
    nodeSites = (locations.groupby('Node').apply(
        lambda x: tuple(x.index)).to_dict())
    checked = set()
    dist = 0
    while True:
        dist += step
        for i, refNode in enumerate(locations['Node'].unique()):
            sites = tuple(locations.loc[locations['Node'] == refNode].index)
            subgraph = nx.ego_graph(G, refNode, radius=dist, distance='length')
            for node in subgraph.nodes():
                if node in checked:
                    continue
                try:
                    distance = nx.shortest_path_length(
                        G, node, refNode, weight='length', method='dijkstra')
                    if distance < distances[node][0]:
                        distances[node] = (distance, nodeSites[refNode])
                except nx.NetworkXNoPath:
                    pass
            checked.update(set(subgraph.nodes()))
        step += (step // 2)
        completion = len(checked) / len(G.nodes())
        logger.info(f'{completion:.1%} complete, distances = {dist}')
        if completion >= maxQuant:
            break
    distances = pd.DataFrame.from_dict(
        distances, orient='index', columns=['Distance', 'SiteIDs'])
    return distances
