# ESNEFT Analysis - Diabetes Inequalities

## Additional documentation and example visualisations

**Note: This documentation is still a work progress and will be updated.**


```python
import pandas as pd
from esneft_tools import synthetic, process, visualise

data = synthetic.emergency()
times = ([
    'incidentDateTime', 'arrivalDateTime', 'registeredDateTime',
    'triagedDateTime', 'seen1DateTime', 'seen2DateTime',
    'fitDischargeDateTime', 'departDateTime'
])
df = pd.melt(data, id_vars='patientID', value_vars=times)
df = df.loc[df['patientID'] == 1]
df = process.prepTime(
    df.dropna(), start='value', end=None, group='variable', interval='1h')
fig = visualise.timeline(df)
fig.show()
```



```python
data = synthetic.emergency()
df = process.prepTime(
    data, start='arrivalDateTime', end='departDateTime',
    group='site', interval='1D')
df = process.processTime(df, normByGroup=True)
fig = plotTheo(df)
fig.show()
```
