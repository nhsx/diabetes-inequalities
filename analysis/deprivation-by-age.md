---
jupyter:
  jupytext:
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
import seaborn as sns
```

```python
df = pd.read_excel('populationbyimdenglandandwales2020 (1).xlsx').set_index('IMD')
```

```python
data = {'age': [], 'imd': []}
for imd in range(1, 10 + 1):
    sub = df.loc[df.index == imd]
    for age in a.index:
        data['age'].extend(int(sub[age]) * [age])
        data['imd'].extend(int(sub[age]) * [imd])
data = pd.DataFrame(data)
```

```python
sns.kdeplot(data=data, x='age', hue='imd')
```

```python
pd.DataFrame(allPop).reset_index().melt(id_vars='index', var_name='IMD (decile)', value_name='')
```

```python
sns.kdeplot(allPop)
```

```python

```
