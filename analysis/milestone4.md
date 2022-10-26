---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.1
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

### LSOA lookup

```python
import logging
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from esneft_tools import download, process, visualise, utils

utils.setVerbosity(logging.INFO)
```

```python
dataDownloader = download.getData()
```

```python
areaLSOA = dataDownloader.fromSource('areaLSOA')
```

```python
data = dataDownloader.fromHost('all')
```

```python
GPsummary = process.getGPsummary(**data, iod_cols='IMD')
```

```python
GPsummary.head()
```

```python
fig = visualise.scatterGP(GPsummary[GPsummary['Status'] == 'Active'], minCount=250)
fig.show()
```

```python
LSOAsummary = process.getLSOAsummary(**data, iod_cols='IMD', bins=5, quantile=True).dropna()
```

```python
LSOAsummary.head()
```

```python
fig = visualise.choroplethLSOA(LSOAsummary, data['geoLSOA'], colour='IMD')
fig.show()
```

```python
utils.writeKey('example.key') # Generate a key - keep it safe and secure (seperate from data!)
```

```python
# Serialise and encrypt pandas dataframe - uses Fernet (symmetric encryption)
utils.writeEncrypt(LSOAsummary.head(), 'example.key', path='lsoa-encrypt.parquet')
```

```python
utils.readEncrypt('lsoa-encrypt.parquet', key='example.key')
```

```python

```
