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


def getGPsummary(gpRegistration, imdLSOA, iod_cols: list = None, **kwargs):
    """ Compute mean IoD per GP practise weighted by patient population """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    summary = (pd
        .merge(gpRegistration, imdLSOA[iod_cols],
               left_on='LSOA11CD', right_index=True)
        .groupby(['OrganisationCode'])
        .apply(_weightedMean, iod_cols))
    summary['Patients'] = (
        gpRegistration.groupby('OrganisationCode')['Patient'].sum())
    return summary


def getLSOAsummary(imdLSOA, gpRegistration, populationLSOA, esneftLSOA,
                   iod_cols: list = None, **kwargs):
    """ Return summary statistics per LSOA """
    iod_cols = _parseIoDcols(imdLSOA, iod_cols)
    # Get GP registration by LSOA
    gpRegistrationByLSOA = gpRegistration.groupby('LSOA11CD')['Patient'].sum()
    summary = pd.merge(
        populationLSOA, gpRegistrationByLSOA,
        left_index=True, right_index=True, how='outer')
    summary['ESNEFT'] = summary.index.isin(esneftLSOA)
    summary = pd.merge(
        summary, imdLSOA[iod_cols],
        left_index=True, right_index=True, how='outer')
    return summary
