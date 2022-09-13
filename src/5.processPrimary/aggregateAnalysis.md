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

```python
import numpy as np
import pandas as pd
from venn import venn
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from matplotlib_venn import venn3, venn2
from sklearn.linear_model import LinearRegression
```

```python
outpatient = pd.read_pickle('../4.processOP/data/OPattendance.pkl')
inpatient = pd.read_pickle('../4.processIP/data/IPadmissions.pkl')
emergency = pd.read_pickle('../4.processAandE/data/AandEattendance.pkl')
primary = pd.read_pickle('../5.processPrimary/data/primaryProcessed-raw.pkl')
```

```python
primary[['CTV3Code', 'CTV3Desc']].value_counts()
```

```python
data = ({
    'Out-patient': set(outpatient['patientID']),
    'In-patient': set(inpatient['patientID']),
    'A&E': set(emergency['patientID']),
    'Primary': set(primary['patientID'])
})
```

```python
# Can we get SNOMED -> CTV3 mapping
# Need to ensure we explicity extract the codes relating to 9 care processes
# We want the full history of patients (first appointment to most recent)
# Can we obtain patients that were referred by Did Not Attend (compare groups 4A and 5A for admission)
```

```python
venn(data)
```

### Show diabetes status per patient

```python
t2d = set(primary.loc[primary['CTV3Desc'] == 'Type II diabetes mellitus', 'patientID'])
t1d = set(primary.loc[primary['CTV3Desc'] == 'Type I diabetes mellitus', 'patientID'])
unknown = set(primary['patientID']) - t2d - t1d
diabetesStatus = ({
    'Type 2':  t2d,
    'Type 1': t1d,
})
```

```python
fig, ax = plt.subplots(figsize=(8,4.5))
venn2(diabetesStatus.values(), diabetesStatus.keys(), ax=ax)
ax.set_title(f'Diabetes Status (Unknown = {len(unknown)})', loc='left')
fig.tight_layout()
```

```python
neverSmoked = set(primary.loc[primary['CTV3Desc'] == 'Never smoked tobacco', 'patientID'])
exSmoker = set(primary.loc[primary['CTV3Desc'] == 'Ex-smoker', 'patientID'])
smoker = set(primary.loc[primary['CTV3Desc'] == 'Smoker', 'patientID'])
unknown = set(primary['patientID']) - neverSmoked - exSmoker - smoker
smokingStatus = ({
    'Never Smoked':  neverSmoked,
    'Ex Smoker': exSmoker,
    'Smoker': smoker,
})
```

```python
fig, ax = plt.subplots(figsize=(8,4.5))
venn3(smokingStatus.values(), smokingStatus.keys(), ax=ax)
ax.set_title(f'Smoking Status (Unknown = {len(unknown)})', loc='left')
fig.tight_layout()
```

```python
def formatRange(x):
    timerange = ''
    for i in ['ReferralDate', 'DischargeDate']:
        if pd.isnull(x[i]):
            time = '?'
        else:
            time = x[i].strftime("%Y %b")
        timerange += time
        if i == 'ReferralDate':
            timerange += ' - '
    return timerange
```

```python
timeExpand = np.timedelta64(2, 'D')
```

```python
outpatientSummary = outpatient.copy()
outpatientSummary['Start'] = outpatientSummary['appointmentDateTime'] - timeExpand
outpatientSummary['End'] = outpatientSummary['appointmentDateTime'] + timeExpand
outpatientSummary['Event'] = 'Outpatient'
outpatientSummary['Referral Period'] = 'N/A'
outpatientSummary['Info'] = outpatientSummary['specialityName']
outpatientSummary['Type'] = 'Outpatient'
outpatientSummary['CodeEventDate'] = outpatientSummary['appointmentDateTime']
outpatientSummary['Value'] = 0
```

```python
emergencySummary = emergency.copy()
emergencySummary['Start'] = emergencySummary['arrivalDateTime'] - timeExpand
emergencySummary['End'] = emergencySummary['arrivalDateTime'] + timeExpand
emergencySummary['Event'] = 'A&E'
emergencySummary['Referral Period'] = 'N/A'
emergencySummary['Info'] = emergencySummary['presentingComplaint']
emergencySummary['Type'] = 'A&E'
emergencySummary['CodeEventDate'] = emergencySummary['arrivalDateTime']
emergencySummary['Value'] = 0
```

```python
cols = ['spellAdmissionDate', 'spellDischargeDate', 'patientID', 'admissionMethod']
names = {'spellAdmissionDate': 'Start', 'spellDischargeDate': 'End', 'admissionMethod': 'Info'}
inpatientSummary = inpatient[cols].rename(names, axis=1).copy()
inpatientSummary['Event'] = 'Admission'
inpatientSummary['Referral Period'] = 'N/A'
inpatientSummary['Type'] = 'Admission'
inpatientSummary['CodeEventDate'] = inpatientSummary['Start']
inpatientSummary['Value'] = 0
```

```python
def fixTime(x, timeExpand):
    """ Expand time to minumum length for visibility """
    if (x['Start'] - x['End']) > timeExpand:
        return pd.Series([x['Start'], x['End']])
    else:
        middle = x['Start'] + (x['End'] - x['Start']) / 2
        return pd.Series([middle - timeExpand, middle + timeExpand])
```

```python
inpatientSummary[['Start', 'End']] = inpatientSummary.apply(fixTime, args=(timeExpand,), axis=1)
```

```python
primarySummary = primary.copy()
primarySummary['Referral Period'] = primarySummary.apply(formatRange, axis=1)
primarySummary['Start'] = primarySummary['CodeEventDate'] - timeExpand
primarySummary['End'] = primarySummary['CodeEventDate'] + timeExpand
primarySummary['Event'] = primarySummary['CTV3Desc']
primarySummary['Info'] = primarySummary['RecodingLabel']
primarySummary['Type'] = 'primary'
primarySummary['Value'] = primarySummary['RecordingValue']
```

```python
cols = ['patientID', 'Referral Period', 'Start', 'End', 'Event', 'Info', 'Type', 'CodeEventDate', 'Value']
primarySummary = pd.concat([
    primarySummary[cols], 
    outpatientSummary[cols], 
    inpatientSummary[cols], 
    emergencySummary[cols]
])
```

```python
primarySummary = primarySummary.loc[primarySummary['patientID'].isin(set(primary['patientID']))]
```

```python
names = ({
    'Haemoglobin A1c level': 'HbA1c',
    'Body mass index - observation': 'BMI',
    'Haemoglobin A1c level - IFCC standardised': 'HbA1c (IFCC)',
    'GFR calculated abbreviated MDRD': 'GFR',
    'O/E - Diastolic BP reading': 'Diastolic BP',
    'Urine microalbumin level': 'Urine Microalbumin',
    'Never smoked tobacco': 'Never Smoked',
    'Type II diabetes mellitus': 'Type 2 Diabetes',
    'Haemoglobin concentration': 'Hemoglobin',
    'Type I diabetes mellitus': 'Type 1 Diabetes',
    'GFR calculated Cockcroft-Gault formula': 'GFR'
})
primarySummary['Event'] = primarySummary['Event'].replace(names)
```

```python
pid = 'RGQ1074991'
#pid = primarySummary['patientID'].drop_duplicates().sample(1).values[0]
```

```python
primarySummary.loc[primarySummary['Info'].isna(), 'Info'] = 'None'
```

```python
sub = primarySummary.loc[primarySummary['patientID'] == pid].copy()
sub = sub.loc[sub['Event'] != 'Date of diagnosis']

fig = px.timeline(
    sub, x_start="Start", x_end="End", y="Event", 
    color="Referral Period", hover_data=['Info'])
fig.update_layout({
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'yaxis_title': '',
    'showlegend': False
})
fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
fig.update_yaxes(showline=True, linewidth=2, linecolor='black')
fig.update_layout(legend=dict(
    title='Referral',
    orientation='h',
    yanchor="top",
    y=-0.1,
    xanchor="left",
    x=0.01
))
fig.show()
```

```python
def summarisePatient(x, eventCounts):
    summary = x['Event'].value_counts().to_dict()
    for event in eventCounts:
        if event not in summary:
            summary[event] = 0
    day = pd.Timedelta('1d')
    sub = x.loc[(x['Type'] == 'primary') & (x['Event'] != 'Date of diagnosis')]
    
    summary['records'] = len(sub)
    codeEvents = sub['CodeEventDate'].dropna()
    if codeEvents.empty:
        summary['recordSpan'] = np.nan
    else:
        summary['recordSpan'] = (codeEvents.max() - codeEvents.min()) / day
    summary['appointments'] = len(sub['CodeEventDate'].dropna().unique())
    summary['referrals'] = len(sub.loc[sub['Referral Period'] != '? ?', 'Referral Period'].unique())
    if (summary['appointments'] - 1) == 0:
        summary['meanWait'] = np.nan
    else:
        summary['meanWait'] = summary['recordSpan'] / (summary['appointments'] - 1)

    events = ['BMI', 'HbA1c (IFCC)', 'GPR']
    for event in events:
        byEvent = sub.loc[
              (sub['Event'] == event) 
            & (sub['Info'] != 'None')
        ]
        if byEvent.empty:
            summary[f'{event}-coef'] = np.nan
        else:
            summary[f'{event}-coef'] = getGradient(byEvent)    
    sub = x.loc[(x['Type'] == 'Admission') & (x['End'] > x['Start'])]
    summary['AdmissionTime'] = ((sub['End'] - sub['Start']) / day).sum()
    return pd.Series(summary).T


def getGradient(pt):
    lm = LinearRegression()
    x = (pt['CodeEventDate'] - pt['CodeEventDate'].min()) 
    x = (x / (365.25 * pd.Timedelta('1d'))).values.reshape(-1, 1)
    if len(x) == 1:
        return np.nan
    y = pt['Value'].values.reshape(-1, 1)
    model = lm.fit(x, y)
    return model.coef_[0][0]
```

```python
eventCounts = primarySummary['Event'].unique()
A = (
    primarySummary
    .groupby('patientID')
    .apply(summarisePatient, eventCounts=eventCounts)
    .reset_index()
    .rename({'level_1': 'feature'}, axis=1)
    .pivot(index='patientID', columns='feature')
    .droplevel(0, axis=1)
)
```
