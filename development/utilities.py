import pandas as pd
import numpy as np

def formatP(p):
    """ Return formatted p-value for title """
    if p > 0.999:
        pformat = '> 0.999'
    elif p < 0.001:
        pformat = '< .001'
    else:
        pformat = '= ' + f'{p:.3f}'[1:]
    if p < 0.001:
        return pformat + ' ***'
    elif p < 0.01:
        return pformat + ' **'
    elif p < 0.05:
        return pformat + ' *'
    else:
        return pformat


def makeChunks(nReps, chunkSize):
    if nReps <= chunkSize:
        return [nReps]
    chunks = [chunkSize for i in range((nReps // chunkSize))]
    remain = nReps % chunkSize
    if remain > 0:
        chunks.append(remain)
    return chunks


def stratifiedPermute(df, stratifyBy, ref, n):
    """ Stratified permutation of ref values """
    originalIndex = df.index
    df = df.set_index(stratifyBy)[[ref]]
    return (
        pd.DataFrame(np.tile(df.values, n), index=df.index)
        .groupby(df.index)
        .transform(np.random.permutation)
        .set_index(originalIndex)
    )


def permutationTest(df, stratifyBy, group, ref, nReps, func, chunkSize=2000):
    null = []
    allData = []
    for chunk in makeChunks(nReps, chunkSize):
        p = stratifiedPermute(df, stratifyBy, ref, chunk)
        p[group] = df[group]
        null.append(p.groupby(group).agg(func))
    null = pd.concat(null, axis=1)
    
    agg = null.agg(['mean', 'std'], axis=1)
    agg[['statistic', 'count']] = df.groupby(group)[ref].agg([func, 'size'])
    agg['z'] = ((agg['statistic'] - agg['mean']) / agg['std'])
    
    return agg, null


def visualiseTable(df, cmap, vmin, vmax, precision=2):
    return (
        df.style.background_gradient(
            cmap=cmap, vmin=vmin, vmax=vmax, axis=None)
        .format(precision=precision)
        .applymap(lambda x: 'color: transparent' if pd.isnull(x) else '')
        .applymap(lambda x: 'background-color: transparent' if pd.isnull(x) else '')
    )