#!/usr/bin/env python

import logging
import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


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


def getGPsummary(gpRegistration, gpPractise, postcodeLSOA, imdLSOA,
                iod_cols: list = None, **kwargs):
    """ Compute mean IoD per GP practise weighted by patient population """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    summary = (pd
        .merge(gpRegistration, imdLSOA[iod_cols],
               left_on='LSOA11CD', right_index=True)
        .groupby(['OrganisationCode'])
        .apply(_weightedMean, iod_cols))
    summary['Patients'] = (
        gpRegistration.groupby('OrganisationCode')['Patient'].sum())
    summary = pd.concat([summary, gpPractise], axis=1)
    summary = pd.merge(
        summary, postcodeLSOA[['Lat', 'Long']], left_on='PCDS',
        right_index=True, how='left')
    summary['ESNEFT'] = summary['PCDS'].isin(
        postcodeLSOA.loc[postcodeLSOA['ESNEFT']].index)
    return summary


def getLSOAsummary(postcodeLSOA, imdLSOA, gpRegistration, populationLSOA,
                   iod_cols: list = None, **kwargs):
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
        lsoaName, populationLSOA,
        gpRegistrationByLSOA, imdLSOA[iod_cols]], axis=1)
    return summary


def _summarisePopulation(x):
    """ Get median Age and total populaiton by LSOA"""
    allAges = []
    for row in x.itertuples():
        allAges.extend([row.Age] * row.Population)
    return pd.Series([np.median(allAges), x['Population'].sum()])
