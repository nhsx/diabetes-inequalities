# Download from: https://download.geofabrik.de/europe/great-britain/england.html

conda activate ox
# Extract region by bbox
osmium extract --bbox 0.477,51.77,1.628,52.61 england-latest.osm.pbf -o esneft.osm
# Filter for roads only
osmium tags-filter -o esngeft-highways.osm esneft.osm nw/highway