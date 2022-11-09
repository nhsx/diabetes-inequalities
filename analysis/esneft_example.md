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
mainDeprivationDomains = ([
    'Income', 'Employment', 'Education',
    'Health', 'Crime', 'Barriers (H&S)', 'Environment',
])
subDeprivationDomains = ([
    'YouthSubDomain', 'AdultSkills', 
    'IndoorsSubDomain', 'OutdoorSubDomain'
])
```

```python
demographics = ['Age (median)', 'EthnicMinority', 'MaleProp']
allData = []
diseases = [i for i in LSOAsummary.columns if i.endswith('prevalance')]
allFeatures = mainDeprivationDomains + demographics
for disease in diseases:
    parcorr = []
    for target in allFeatures + subDeprivationDomains:
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
order = allData.abs().mean(axis=1).sort_values(ascending=False)
allData = allData.reindex(order.index)
```

```python
vmax = allData.max().max()
vmin = allData.min().min()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12,7))
g1 = sns.heatmap(
    data=allData.loc[allData.index.isin(allFeatures)], 
    yticklabels=1, cmap='bwr', vmin=vmin, vmax=vmax, center=0, ax=ax1)
_ = g1.set_xticklabels(g1.get_xticklabels(), rotation=45)
g2 = sns.heatmap(
    data=allData.loc[allData.index.isin(subDeprivationDomains)], 
    yticklabels=1, cmap='bwr', vmin=vmin, vmax=vmax, center=0, ax=ax2)
_ = g2.set_xticklabels(g2.get_xticklabels(), rotation=45)
fig.tight_layout()
fig.savefig('plots/deprivation-vs-prevalence.png', dpi=300)
```

```python
iod = 'AdultSkills'
```

```python
fig, ax = plt.subplots()
sns.kdeplot(data=GPsummary, x=iod, y='DM-prevalance', fill=True, ax=ax)
sns.regplot(data=GPsummary, x=iod, y='DM-prevalance', order=1, scatter=False, ax=ax)
ax.set_ylim(0, 0.15)
ax.set_ylabel('Diabetes prevalance')
fig.tight_layout()
fig.savefig(f'plots/national_prevalance_by_{iod}.png', dpi=300)
```

```python
metrics = ({'DM019-BP': 'BP < 140/80 mmHg', 'DM020-HbA1c': 'IFCC-HbA1c < 58 mmol/mol'})
fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharex=True, sharey=True)
axes = axes.flatten()
for i, (metric, label) in enumerate(metrics.items()):
    rho, p = spearmanr(GPsummary[[iod, metric]].dropna())
    sns.kdeplot(data=GPsummary, x=iod, y=metric, fill=True, ax=axes[i])
    sns.regplot(data=GPsummary, x=iod, y=metric, scatter=False, ax=axes[i])
    axes[i].set_title(f"{label} (Rho  = {rho:.2f}, {formatP(p)})", loc='left')
    axes[i].set_ylim(0.2, 0.9)
axes[0].set_ylabel('Proportion of patients meeting treatment target')
fig.tight_layout()
fig.savefig(f'plots/dm-metrics-by-{iod}.png', dpi=300)
```

```python
df = LSOAsummary[['Age (median)', f'{iod} ({name})', 'DM-prevalance', 'Population']].dropna().copy()
df['Age'] = pd.qcut(df['Age (median)'], 5)
table = (
    df.groupby(['Age', f'{iod} ({name})'])
    .apply(lambda x: (np.average(x['DM-prevalance'], weights=x['Population'])) * 100_000)
    .reset_index()
    .pivot(index='Age', columns=f'{iod} ({name})')
    .droplevel(0, axis=1)
)
fig, ax = plt.subplots()
sns.heatmap(table, cmap='viridis', ax=ax)
ax.set_title(f'Diabetes Prevalance by Age and {iod}', loc='left')
fig.tight_layout()
fig.savefig(f'plots/prevalance_by_age_by_{iod}.png', dpi=300)
```

```python
fig, ax = plt.subplots()
sns.kdeplot(data=LSOAsummary, x=iod, y='EthnicMinority', fill=True, ax=ax)
sns.regplot(data=LSOAsummary, x=iod, y='EthnicMinority', order=1, scatter=False, ax=ax)
ax.set_ylabel('Proportion of Ethnic Minority')
fig.tight_layout()
fig.savefig(f'plots/ethnicity_by_{iod}.png', dpi=300)
```

```python
fig, ax = plt.subplots()
sns.kdeplot(data=LSOAsummary.dropna(), x='Age (median)', hue=f'{iod} ({name})', common_norm=False, ax=ax)
fig.tight_layout()
fig.savefig(f'plots/age-by-{iod}.png', dpi=300)
```

```python
prev_by_imd = sns.lmplot(
    data=LSOAsummary.dropna(), x='Age (median)', 
    y='DM-prevalance', hue=f'{iod} ({name})', scatter=False)
prev_by_imd.savefig(f'plots/prevalance-age-by-{iod}.png', dpi=300)
```

```python
fig = visualise.scatterGP(GPsummary[GPsummary['Status'] == 'Active'], minCount=250)
fig.show()
fig.write_image('plots/GP-locations.png')
```

```python
fig = visualise.choroplethLSOA(LSOAsummary, data['geoLSOA'], colour='IMD')
fig.write_image('plots/LSOA-choropleth.png')
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
