FROM python:3.10-slim

COPY . /repo
WORKDIR /repo
ENV PIP_ROOT_USER_ACTION=ignore

RUN    apt-get -y update \
    && apt-get -y install git \
    && apt-get update \
    && apt-get install -y binutils libproj-dev gdal-bin \
    && pip install 'numpy>=1.22' \
                   'pandas>=1.4' \
                   'matplotlib>=3.5' \
                   'networkx>=2.8' \
                   'pyproj>=3.3' \
                   'requests>=2.28' \
                   'Rtree>=1.0' \
                   'Shapely>=1.8' \
                   'gdal>=3.5.2' \
                   'geopandas>=0.11' \
    && pip install osmnx \
    && pip install .

CMD ["bash"]
