#!/usr/bin/env python

import random
import logging
import numpy as np
import pandas as pd
from esneft_tools import download
from datetime import timedelta, datetime


logger = logging.getLogger(__name__)


def _randomDate(start, delta='1Y'):
    """ Generate random date in range """
    if pd.isnull(start):
        return start
    delta = pd.Timedelta(delta)
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)


def emergency(size: int = 10_000, seed: int = 42):
    np.random.seed(seed)
    random.seed(seed)
    getData = download.getData()
    postcodes = getData.fromHost('postcodeLSOA')
    esneftLSOA = getData.fromHost('esneftLSOA')
    postcodes = postcodes[postcodes.isin(esneftLSOA)].index
    # Define fewer patients then entries
    nPatients = int(size*0.61) if size > 1 else 1
    inc1 = datetime.strptime('1/1/2018', '%d/%m/%Y')

    data = pd.DataFrame({
        'site': np.random.choice(
            ['Ipswich', 'Colchester'], size=size, p=[0.52, 0.48]),
        'AEDid': range(size),
        'patientID': np.random.choice(range(nPatients), size=size),
        'Age': np.random.randint(0, 100, size=size),
        'Sex': np.random.choice(
            ['Female', 'Male', 'Unknown'],
            p=[0.51, 0.48, 0.01], size=size),
        'Ethnicity': np.random.choice(
            ['White', 'Unknown', 'Other', 'Mixed', 'Asian', 'Black'],
            p=[0.79, 0.15, 0.02, 0.02, 0.01, 0.01], size=size),
        'Postcode': np.random.choice(postcodes, size=size),
        'presentingSymptoms': np.random.choice(
            ['Chest pain', 'General Weakness', 'Abdominal pain', 'Falls'],
            p=[0.31, 0.29, 0.24, 0.16], size=size),
        'disposalMethod': np.random.choice(
            ['Discharged', 'Admitted', 'Discharged - follow up', 'Other'],
            p=[0.36, 0.33, 0.21, 0.1], size=size),
        'incidentDateTime': [_randomDate(inc1, '365d') for i in range(size)],
    })

    data['arrivalDateTime'] = data['incidentDateTime'].apply(_randomDate, args=('4d',))
    data['registeredDateTime'] = data['arrivalDateTime'].apply(_randomDate, args=('4m',))
    data['triagedDateTime'] = data['registeredDateTime'].apply(_randomDate, args=('32m',))
    data['seen1DateTime'] = data['triagedDateTime'].apply(_randomDate, args=('2h',))
    data['seen2DateTime'] = data['seen1DateTime'].apply(_randomDate, args=('2h',))
    data['fitDischargeDateTime'] = data['seen2DateTime'].apply(_randomDate, args=('90m',))
    data['departDateTime'] = data['fitDischargeDateTime'].apply(_randomDate, args=('10m',))

    data['incidentDateTime'] = data['incidentDateTime'].apply(
        lambda x :np.datetime64('NaT') if np.random.random() < 0.58 else x)
    data['registeredDateTime'] = data['registeredDateTime'].apply(
        lambda x :np.datetime64('NaT') if np.random.random() < 0.51 else x)
    data['triagedDateTime'] = data['triagedDateTime'].apply(
        lambda x :np.datetime64('NaT') if np.random.random() < 0.1 else x)
    data['seen1DateTime'] = data['seen1DateTime'].apply(
        lambda x :np.datetime64('NaT') if np.random.random() < 0.05 else x)
    data['seen2DateTime'] = data.apply(
        lambda x : (np.datetime64('NaT') if (np.random.random() < 0.92
                    or pd.isnull(x['seen1DateTime'])) else x['seen2DateTime']),
                    axis = 1)
    data['fitDischargeDateTime'] = data['fitDischargeDateTime'].apply(
        lambda x :np.datetime64('NaT') if np.random.random() < 0.37 else x)
    return data
