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


def getGPsummary(gp_reg, imd, quintile: bool = False, iod_cols: list = None):
    """ Compute mean IoD per GP practise weighted by patient population """
    iod_cols = _parseIoDcols(imd, iod_cols)
    summary = (pd
        .merge(gp_reg, imd[iod_cols], left_on='LSOA11CD', right_index=True)
        .groupby(['OrganisationCode'])
        .apply(_weightedMean, iod_cols))
    if quintile:
        summary = summary.apply(lambda x: pd.cut(x, 5, labels=[1,2,3,4,5]))
    summary['Patients'] = gp_reg.groupby('OrganisationCode')['Patient'].sum()
    return summary


def getLSOAsummary(imd, gp_reg, pop_summary,
                   quintile: bool = False, iod_cols: list = None):
    """ Return summary statistics per LSOA """
    iod_cols = _parseIoDcols(imd, iod_cols)
    if quintile:
        imd = imd.apply(lambda x: pd.cut(x, 5, labels=[1,2,3,4,5]))
    # Get GP registration by LSOA
    gp_reg_by_lsoa = gp_reg.groupby('LSOA11CD')['Patient'].sum()
    summary = pd.merge(
        pop_summary, gp_reg_by_lsoa,
        left_index=True, right_index=True, how='outer')
    summary = pd.merge(
        summary, imd[iod_cols], left_index=True, right_index=True, how='outer')
    return summary
