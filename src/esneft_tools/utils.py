#!/usr/bin/env python


import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from cryptography.fernet import Fernet
from pandas.api.types import is_object_dtype
from pandas.api.types import is_datetime64_any_dtype as is_datetime


logger = logging.getLogger(__name__)


def setVerbosity(
        level=logging.INFO, handler=logging.StreamHandler(),
        format='%(name)s - %(levelname)s - %(message)s'):
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    esneft_logger = logging.getLogger('esneft_tools')
    esneft_logger.setLevel(level)
    esneft_logger.addHandler(handler)


def formatP(p):
    """ Return formatted p for title """
    pformat = 'p '
    if p > 0.999:
        pformat += '> 0.999'
    elif p < 0.001:
        pformat += '< .001'
    else:
        pformat += '= ' + f'{p:.3f}'[1:]
    if p < 0.001:
        return pformat + ' ***'
    elif p < 0.01:
        return pformat + ' **'
    elif p < 0.05:
        return pformat + ' *'
    else:
        return pformat


def writeKey(path):
    key = Fernet.generate_key()
    with open(path, 'wb') as fh:
        fh.write(key)


def readKey(path):
    with open(path, 'rb') as fh:
        key = fh.read()
    return Fernet(key)


def writeEncrypt(df, key, path=None):
    f = readKey(key)
    df = df.reset_index()
    cols = df.columns
    for col in cols:
        name = f'{col}-encrypted'
        dtype = df[col].dtype
        if is_object_dtype(df[col]):
            df[name] = df[col]
        elif dtype in [float, int, bool]:
            df[name] = df[col].apply(lambda x: repr(x))
        elif dtype == 'category':
            name = f'{col}-pd.{repr(dtype)}-encrypted'
            df[name] = df[col].apply(lambda x: repr(x))
        else:
            try:
                eval(f'pd.{repr(df.iloc[0][col])}')
            except:
                logging.error(f'Cannot encrypt dtype {dtype}')
                continue
            df[name] = df[col].apply(lambda x: f'pd.{repr(x)}')
        name_encrypt = f.encrypt(name.encode('utf-8')).decode('utf-8')
        df[name_encrypt] = df[name].apply(
            lambda x: f.encrypt(x.encode('utf-8')))
        df = df.drop([name, col], axis=1)
    if path is not None:
        df.to_parquet(path)
    return df


def readEncrypt(path, key):
    df = pd.read_parquet(path)
    f = readKey(key)
    encrypted_cols = df.columns
    for col_name_encrypt in encrypted_cols:
        drop = [col_name_encrypt]
        col_name = f.decrypt(col_name_encrypt.encode('utf-8')).decode('utf-8')
        if not col_name.endswith('-encrypted'):
            continue
        name = col_name.removesuffix('-encrypted')
        df[name] = df[col_name_encrypt].apply(
            lambda x: f.decrypt(x).decode('utf-8'))
        if 'pd.Categorical' in name:
            pos = name.find('pd.Categorical')
            dtype = eval(name[pos:])
            # Fix underlying dtype
            col = name[:pos-1]
            df[col] = df[name].astype(dtype.categories.dtype)
            # Then convert back to category
            df[col] = df[col].astype(dtype)
            drop.append(name)
        else:
            try:
               df[name] = df[name].apply(lambda x: eval(x))
            except:
               pass
        df = df.drop(drop, axis=1)
    df = df.set_index(df.columns[0])
    return df
