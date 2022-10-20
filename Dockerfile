FROM python:3.10-slim

COPY . /repo
WORKDIR /repo
ENV PIP_ROOT_USER_ACTION=ignore

RUN    apt-get -y update \
    && apt-get -y install git \
    && apt-get update \
    && apt-get install python3-dev \
    && apt-get install gdal-bin \
    && apt-get install libgdal-dev \
    && pip install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}') localtileserver \
    && pip install 'geopandas>=0.11' \
                   'matplotlib>=3.5' \
                   'networkx>=2.8' \
                   'numpy>=1.22' \
                   'pandas>=1.4' \
                   'pyproj>=3.3' \
                   'requests>=2.28' \
                   'Rtree>=1.0' \
                   'Shapely==1.9' \
    && pip install osmnx \
    && pip install .

CMD ["bash"]
