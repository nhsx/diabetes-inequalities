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
import statsmodels.api as sm
```

```python
data = sm.datasets.china_smoking.load_pandas()

mat = np.asarray(data.data)

tables = [np.reshape(x.tolist(), (2, 2)) for x in mat]
```

```python
A = np.bincount(2 * np.array([1,1,1,0,1,1]) + np.array([1,0,0,1,1,1]), minlength=4).reshape(2,2)
A
```

```python
np.rot90(np.flipud(A))
```

```python
tables = np.array([[[ 410,  685], [5334, 7573]],[[ 686, 1031],[0,0]]])
st = sm.stats.StratifiedTable(tables)
```

```python
st.summary()
```

```python

```
