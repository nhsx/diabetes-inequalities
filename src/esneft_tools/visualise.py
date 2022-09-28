#!/usr/bin/env python

import logging
import pandas as pd
import plotly.express as px


logger = logging.getLogger(__name__)


def choropleth(data, geojson, colour, location=None, cmap='viridis'):
    assert colour in data.columns
    if location is None:
        location = data.index.name if data.index.name else 'index'
        data = data.reset_index()
    else:
        assert location in data.columns
    fig = px.choropleth_mapbox(
        data, geojson=geojson,
        locations=location, color=colour,
        color_continuous_scale=cmap,
        mapbox_style="carto-positron",
        zoom=8.5, center = {'lat': 52.08, 'lon': 1.02},
        width=870, height=700, opacity=0.5
    )
    return fig
