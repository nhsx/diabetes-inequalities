#!/usr/bin/env python

import sys
import logging
import matplotlib
import numpy as np
import pandas as pd
import plotly.express as px
from collections import defaultdict


logger = logging.getLogger(__name__)


try:
    import osmnx as ox
except ModuleNotFoundError:
    logger.error('OSMNX not found - some features are unavailable.')


def choroplethLSOA(
        LSOAsummary, geojson, colour, location=None,
        hover=None, cmap='viridis'):
    assert colour in LSOAsummary.columns
    if (hover is None) and ('LSOA11NM' in LSOAsummary.columns):
        hover = ['LSOA11NM']
    if location is None:
        location = LSOAsummary.index.name if LSOAsummary.index.name else 'index'
        LSOAsummary = LSOAsummary.reset_index()
    else:
        assert location in LSOAsummary.columns
    fig = px.choropleth_mapbox(
        LSOAsummary, geojson=geojson,
        locations=location, color=colour,
        hover_data=hover,
        color_continuous_scale=cmap,
        mapbox_style="carto-positron",
        zoom=8.5, center = {'lat': 52.08, 'lon': 1.02},
        width=870, height=700, opacity=0.5
    )
    return fig


def scatterGP(GPsummary, minCount=1, palette=px.colors.qualitative.Plotly):
    GPsummary = GPsummary.copy()
    # Aggregate settings with too few counts
    count = GPsummary['PrescribingSetting'].value_counts()
    tooFew = count[count < minCount].index
    GPsummary['PrescribingSetting'] = GPsummary['PrescribingSetting'].apply(
        lambda x: 'Other' if x in tooFew else x
    )
    GPsummary['IMD'] = GPsummary['IMD'].apply(lambda x: f'{x:.3f}')
    GPsummary['OpenDate'] = GPsummary['OpenDate'].astype(str)
    GPsummary['Patient'] = GPsummary['Patient'].fillna(-1).astype(int)
    fig = px.scatter_mapbox(
        GPsummary, lat='Lat', lon='Long',
        hover_name='OrganisationName',
        hover_data=['PCDS', 'Status', 'IMD', 'Patient', 'OpenDate'],
        color='PrescribingSetting',
        color_discrete_sequence=palette,
        mapbox_style="carto-positron",
        zoom=8.2, center = {'lat': 52.08, 'lon': 1.02},
        width=870, height=600, opacity=1

    )
    fig.update_layout(legend=dict(
        orientation='h', yanchor='bottom', y=1.02,
        xanchor='right', x=1, title=None))
    return fig


def _setNodeProperties(
        G, distances, vmin=0, vmax=0.9, quantile=True,
        cmap='viridis_r', size=10):
    if quantile:
        vmax = np.quantile(distances['Distance'], vmax)
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.cm.get_cmap(cmap)
    colours = []
    sizes = []
    for node in G.nodes():
        if node not in distances.index:
            colour = (1,1,1,1)
            size = 0
        else:
            colour = cmap(norm(distances.loc[node, 'Distance']))
            size = 10
        colours.append(colour)
        sizes.append(size)
    return colours, sizes


def plotTravelTime(
        G, distances, quantile=True, maxQuant=0.95,
        cmap='viridis_r', size=10, dpi=300, alpha=0.8,
        figsize=(15,15),out=None):
    colours, sizes = _setNodeProperties(
        G, distances, vmin=0, vmax=maxQuant,
        quantile=quantile, cmap=cmap, size=size)
    fig, ax = ox.plot_graph(
        G, node_color=colours, node_size=sizes,
        node_alpha=alpha, figsize=figsize,
        save=(out is not None), dpi=dpi, filepath=out)
    return fig, ax


def timeline(df: pd.DataFrame, colour='group'):
    if 'Freq.' in df.columns:
        fig = px.timeline(
            df, x_start='start', x_end='end', y='group',
            color='Freq.', range_color=(0, 1),
            color_continuous_scale=px.colors.sequential.gray_r)
        # Order groups by frequency
        order = df.groupby('group')['Freq.'].sum().sort_values().index
    else:
        fig = px.timeline(
            df, x_start='start', x_end='end', y='group',
            color=colour, hover_data=['group'])
        order = df.groupby('group')['end'].max().sort_values().index
    fig.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'yaxis_title': '',
        'showlegend': False
    })
    fig.update_xaxes(
        showline=True, linewidth=2, linecolor='black')
    fig.update_yaxes(
        showline=True, linewidth=2,
        categoryarray=order, linecolor='black')
    fig.update_layout(legend=dict(
        orientation='h',
        yanchor='top', y=-0.1,
        xanchor='left', x=0.01
    ))
    return fig
