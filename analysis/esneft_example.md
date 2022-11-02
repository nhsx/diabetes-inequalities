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
from scipy.stats import spearmanr
from pingouin import partial_corr
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
data['qof'] = dataDownloader.fromSource('qof')
```

```python
deprivationCols = ([
    'IMD', 'Income', 'Employment', 'Education', 'Health', 'Crime',
    'Barriers (H&S)', 'Environment', 'IDACI', 'IDAOPI', 'YouthSubDomain',
    'AdultSkills', 'Barriers (Geo)', 'Barriers (Wider)', 
    'IndoorsSubDomain', 'OutdoorSubDomain'
])
```

```python
GPsummary = process.getGPsummary(**data, iod_cols=deprivationCols)
```

```python
bins = 5
quantile = True
name = f'q{bins}' if quantile else f'i{bins}'
LSOAsummary = process.getLSOAsummary(**data, iod_cols=deprivationCols, bins=bins, quantile=True).dropna()
```

```python
fig, ax = plt.subplots()
sns.kdeplot(data=GPsummary, x='IMD', y='DM-prevalance', fill=True, ax=ax)
sns.regplot(data=GPsummary, x='IMD', y='DM-prevalance', order=2, scatter=False, ax=ax)
ax.set_ylim(0, 0.15)
ax.set_ylabel('Diabetes prevalance')
fig.tight_layout()
fig.savefig('national_prevalance_by_imd.png', dpi=300)
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
fig.savefig('dm-metrics-by-imd.png', dpi=300)
```

```python
fig = visualise.scatterGP(GPsummary[GPsummary['Status'] == 'Active'], minCount=250)
fig.show()
fig.write_image('GP-locations.png')
```

```python
deprivationCols = ([
    'Income', 'Employment', 'Education',
    'Health', 'Crime', 'Barriers (H&S)', 'Environment',
])
subDeprivation = ([
    'YouthSubDomain', 'AdultSkills', 
    'IndoorsSubDomain', 'OutdoorSubDomain'
])
```

```python
demographics = ['Age (median)', 'EthnicMinority', 'MaleProp']
allData = []
diseases = [i for i in LSOAsummary.columns if i.endswith('prevalance')]
allFeatures = deprivationCols + demographics
for disease in diseases:
    parcorr = []
    for target in allFeatures + subDeprivation:
        if target in ['YouthSubDomain', 'AdultSkills']:
            covars = [i for i in allFeatures if i != 'Education']
        elif target in ['IndoorsSubDomain', 'OutdoorSubDomain']:
            covars = [i for i in allFeatures if i != 'Environment']
        else:
            covars = [i for i in allFeatures if i != target]
        corr = partial_corr(
            data=LSOAsummary, x=target, y=disease, 
            covar=covars, method='spearman')
        corr.index = [target]
        parcorr.append(corr)
    parcorr = pd.concat(parcorr).sort_values('r', ascending=False)['r'].rename(disease.split('-')[0])
    allData.append(parcorr)
allData = pd.concat(allData, axis=1)
order = allData.mean(axis=1).sort_values(ascending=False)
allData = allData.reindex(order.index)
(
    allData.loc[allData.index.isin(allFeatures)]
    .style.background_gradient(vmin=-1, vmax=1, cmap='bwr', axis=None)
    .format(precision=1)
)
```

```python
(
    allData.loc[allData.index.isin(subDeprivation)]
    .style.background_gradient(vmin=-1, vmax=1, cmap='bwr', axis=None)
    .format(precision=1)
)
```

```python
deprivation = 'IMD'
```

```python
df = LSOAsummary[['Age (median)', f'{deprivation} ({name})', 'DM-prevalance', 'Population']].dropna().copy()
df['Age'] = pd.qcut(df['Age (median)'], 10)
table = (
    df.groupby(['Age', f'{deprivation} ({name})'])
    .apply(lambda x: (np.average(x['DM-prevalance'], weights=x['Population'])) * 100_000)
    .reset_index()
    .pivot(index='Age', columns=f'{deprivation} ({name})')
    .droplevel(0, axis=1)
)
fig, ax = plt.subplots()
sns.heatmap(table, cmap='viridis', ax=ax)
ax.set_title('Diabetes Prevalance by Age and IMD', loc='left')
fig.tight_layout()
```

```python
sns.kdeplot(data=LSOAsummary.dropna(), x='Age (median)', y=deprivation, fill=True)
```

```python
fig, ax = plt.subplots()
sns.kdeplot(data=LSOAsummary.dropna(), x='Age (median)', hue=f'{deprivation} ({name})', ax=ax)
fig.tight_layout()
fig.savefig('age-by-imd.png', dpi=300)
```

```python
prev_by_imd = sns.lmplot(
    data=LSOAsummary.dropna(), x='Age (median)', 
    y='DM-prevalance', hue=f'{deprivation} ({name})', scatter=False)
prev_by_imd.savefig('prevalance-by-age_imd.png', dpi=300)
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
sns.scatterplot(data=postcodeLSOA, x='Distance', y='IMD', hue='IMD (q5)')
```

geoLSOA = dataDownloader.fromSource('geoLSOA')
imdLSOA = dataDownloader.fromSource('imdLSOA')
postcodeLSOA = dataDownloader.fromSource('postcodeLSOA')
gpRegistration = dataDownloader.fromSource('gpRegistration')
gpPractise = dataDownloader.fromSource('gpPractise')
gpStaff = dataDownloader.fromSource('gpStaff')
populationLSOA = dataDownloader.fromSource('populationLSOA')
areaLSOA = dataDownloader.fromSource('areaLSOA')
