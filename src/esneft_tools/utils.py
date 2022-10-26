#!/usr/bin/env python


import os
import logging
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
        dtype = df[col].dtype
        if dtype == float:
            name = f'{col}-float'
        elif dtype == int:
            name = f'{col}-int'
        elif dtype == bool:
            name = f'{col}-bool'
        elif is_datetime(df[col]):
            name = f'{col}-dt'
        elif is_object_dtype(df[col]):
            name = f'{col}-object'
            df.loc[df[col].isna(), col] = ''
        else:
            logging.error(f'Cannot encrypt column {col} with dtype {dtype}.')
            continue
        if name.endswith('-dt'):
            df[name] = df[col].dt.strftime('%Y-%B-%d-%H-%M-%S')
        else:
            df[name] = df[col].apply(lambda x: repr(x))
        name_encrypt = f.encrypt(f'{name}-encrypted'.encode('utf-8')).decode('utf-8')
        df[name_encrypt] = df[name].apply(
            lambda x: f.encrypt(str(x).encode('utf-8')))
        df = df.drop([name, col], axis=1)
    if path is not None:
        df.to_parquet(path)
    return df


def readEncrypt(path, key):
    df = pd.read_parquet(path)
    f = readKey(key)
    encrypted_cols = df.columns
    for col_name_encrypt in encrypted_cols:
        col_name = f.decrypt(col_name_encrypt.encode('utf-8')).decode('utf-8')
        if not col_name.endswith('-encrypted'):
            continue
        name = col_name.removesuffix('-encrypted')
        df[name] = df[col_name_encrypt].apply(
            lambda x: f.decrypt(x).decode('utf-8'))
        col, dtype = name.rsplit('-', 1)
        if dtype == 'dt':
            df[col] = df[name].apply(
                lambda x: pd.NaT if x == 'nan' else
                datetime.strptime(x, '%Y-%B-%d-%H-%M-%S'))
        elif dtype == 'object':
            df[col] = df[name]
            df.loc[df[col] == '', col] = np.nan
        else:
            df[col] = df[name].astype(eval(dtype))
        df = df.drop([name, col_name_encrypt], axis=1)
    df = df.set_index(df.columns[0])
    return df
