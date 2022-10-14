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
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
from esneft_tools.utils import setVerbosity, formatP
from esneft_tools import download, process, visualise

setVerbosity(logging.INFO)
```

```python
dataDownloader = download.getData()
```

```python
data = dataDownloader.fromHost('all')
```

```python
GPsummary = process.getGPsummary(**data, iod_cols='IMD')
```

```python
fig, ax = plt.subplots()
sns.kdeplot(data=GPsummary, x='IMD', y='DM-prevalance', fill=True, ax=ax)
sns.regplot(data=GPsummary, x='IMD', y='DM-prevalance', order=2, scatter=False, ax=ax)
ax.set_ylim(0, 0.15)
fig.tight_layout()
```

```python
metrics = ({'DM019-BP': 'BP < 140/80 mmHg', 'DM020-HbA1c': 'IFCC-HbA1c < 58 mmol/mol'})
fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharex=True, sharey=True)
axes = axes.flatten()
for i, (metric, label) in enumerate(metrics.items()):
    rho, p = spearmanr(GPsummary[['IMD', metric]].dropna())
    sns.kdeplot(data=GPsummary, x='IMD', y=metric, fill=True, ax=axes[i])
    sns.regplot(data=GPsummary, x='IMD', y=metric, scatter=False, ax=axes[i])
    axes[i].set_title(f"{label} (Rho  = {rho:.2f}, p {formatP(p)})", loc='left')
    axes[i].set_ylim(0.2, 0.9)
axes[0].set_ylabel('Proportion of patients meeting treatment target')
fig.tight_layout()
```

```python
fig = visualise.scatterGP(GPsummary[GPsummary['Status'] == 'Active'], minCount=250)
fig.show()
fig.write_image('GP-locations.png')
```

```python
bins = 5
quantile = True
name = f'q{bins}' if quantile else f'i{bins}'
LSOAsummary = process.getLSOAsummary(**data, iod_cols='IMD', bins=bins, quantile=True)#.dropna()
```

```python
sns.histplot(data=LSOAsummary.dropna(), x='IMD', hue=f'IMD ({name})', stat='probability')
```

```python
sns.lmplot(
    data=LSOAsummary.dropna(), x='Age (median)', 
    y='DM-prevalance', hue=f'IMD ({name})', scatter=False)
```

```python
fig = visualise.choroplethLSOA(LSOAsummary, data['geoLSOA'], colour='IMD')
fig.write_image('LSOA-choropleth.png')
```

```python
activeGP = GPsummary.loc[
      (GPsummary['Status'] == 'Active')
    & (GPsummary['PrescribingSetting'] == 'GP Practice')
].copy()
# Are patients registered to their nearest GP?
distances = process.computeTravelDistance(data['esneftOSM'], activeGP, maxQuant=0.99)
distances.to_pickle('.data-cache/OSM-GPdistance.pkl')
```

```python
distances = pd.read_pickle('.data-cache/OSM-GPdistance.pkl')
fig, ax = visualise.plotTravelTime(
    data['esneftOSM'], distances, maxQuant=0.95, out='GP-accessibility.png')
```

```python
postcodeLSOA = data['postcodeLSOA']

postcodeLSOA = pd.merge(
    postcodeLSOA.loc[postcodeLSOA['Node'] != -1],
    distances,
    left_on='Node', right_index=True, how='left')

postcodeLSOA = postcodeLSOA.groupby(['LSOA11CD', 'LSOA11NM'])['Distance'].mean().reset_index().set_index('LSOA11CD')
```

```python
postcodeLSOA = pd.merge(
    postcodeLSOA,
    LSOAsummary[['IMD', 'IMD (q5)']],
    left_index=True, right_index=True, how='left')
```

```python
postcodeLSOA.head()
```

```python
sns.scatterplot(data=postcodeLSOA, x='Distance', y='IMD', hue='IMD (q5)')
```

```python
GPsummary
```

```python

```

geoLSOA = dataDownloader.fromSource('geoLSOA')
imdLSOA = dataDownloader.fromSource('imdLSOA')
postcodeLSOA = dataDownloader.fromSource('postcodeLSOA')
gpRegistration = dataDownloader.fromSource('gpRegistration')
gpPractise = dataDownloader.fromSource('gpPractise')
gpStaff = dataDownloader.fromSource('gpStaff')
populationLSOA = dataDownloader.fromSource('populationLSOA')
areaLSOA = dataDownloader.fromSource('areaLSOA')
