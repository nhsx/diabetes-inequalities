#!/usr/bin/env python

import logging
import pandas as pd
import plotly.express as px


logger = logging.getLogger(__name__)


def choroplethLSOA(LSOAsummary, geojson, colour, location=None, cmap='viridis'):
    assert colour in LSOAsummary.columns
    if location is None:
        location = LSOAsummary.index.name if LSOAsummary.index.name else 'index'
        LSOAsummary = LSOAsummary.reset_index()
    else:
        assert location in LSOAsummary.columns
    fig = px.choropleth_mapbox(
        LSOAsummary, geojson=geojson,
        locations=location, color=colour,
        hover_data=['LSOA11NM'],
        color_continuous_scale=cmap,
        mapbox_style="carto-positron",
        zoom=8.5, center = {'lat': 52.08, 'lon': 1.02},
        width=870, height=700, opacity=0.5
    )
    return fig


def scatterGP(GPsummary):
    GPsummary = GPsummary.copy()
    GPsummary['IMD'] = GPsummary['IMD'].apply(lambda x: f'{x:.3f}')
    GPsummary['OpenDate'] = GPsummary['OpenDate'].astype(str)
    GPsummary['Patients'] = GPsummary['Patients'].fillna(-1).astype(int)
    fig = px.scatter_mapbox(
        GPsummary, lat='Lat', lon='Long',
        hover_name='OrganisationName',
        hover_data=['PCDS', 'Status', 'IMD', 'Patients', 'OpenDate'],
        color='PrescribingSetting',
        color_discrete_sequence=px.colors.qualitative.Plotly,
        mapbox_style="carto-positron",
        zoom=8.2, center = {'lat': 52.08, 'lon': 1.02},
        width=870, height=600, opacity=0.5

    )
    fig.update_layout(legend=dict(
        orientation='h', yanchor='bottom', y=-0.2, xanchor='left', x=0,
        title=None))
    return fig


def scatterGP2(LSOAsummary, GPsummary, geojson, colour, location=None, cmap='viridis'):
    assert colour in LSOAsummary.columns
    if location is None:
        location = LSOAsummary.index.name if LSOAsummary.index.name else 'index'
        LSOAsummary = LSOAsummary.reset_index()
    else:
        assert location in LSOAsummary.columns
    fig = px.choropleth_mapbox(
        LSOAsummary, geojson=geojson,
        locations=location, color=colour,
        hover_data=['LSOA11NM'],
        color_continuous_scale=cmap,
        mapbox_style="carto-positron",
        zoom=8.5, center = {'lat': 52.08, 'lon': 1.02},
        width=870, height=700, opacity=0.5
    )
    fig.update_layout(coloraxis_colorbar_x=False)
    fig2 = px.scatter_mapbox(
        GPsummary, lat='Lat', lon='Long',
        hover_name='OrganisationName', color='PrescribingSetting',
        color_discrete_sequence=px.colors.qualitative.Plotly

    )
    for trace in fig2.data:
        fig.add_trace(trace)
    for i, frame in enumerate(fig.frames):
        fig.frames[i].data += (fig2.frames[i].data[0],)
    return fig
