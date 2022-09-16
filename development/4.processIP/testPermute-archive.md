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
```

```python
df = pd.DataFrame({
    'A': [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
    'B': [1, 1, 1, 2, 2, 1, 1, 2, 2, 2],
    'C': [1, 3, 5, 7, 4, 1, 3, 9, 0, 3]
})
```

```python
n = 20000
```

```python
def customPermute(df, groupBy, col, n):
    """ Permute permutation """
    originalIndex = df.index
    df = df.set_index(groupBy)[[col]]
    return (
        pd.DataFrame(np.tile(df.values, n), index=df.index)
        .groupby(df.index)
        .transform(np.random.permutation)
        .set_index(originalIndex)
    )
```

```python
df
```

```python
a
```

```python
df.groupby(['A', 'B']).transform(np.random.permutation)
```

```python

```
