# ESNEFT Analysis - Diabetes Inequalities

[![status: experimental](https://github.com/GIScience/badges/raw/master/status/experimental.svg)](https://github.com/GIScience/badges#experimental)

## Table of contents

  * [Installation](#installation)
  * [Workflow](#workflow)
    * [Generate Example Data](#generate-example-data)
  * [License](#license)
  * [Contact](#contact)


## Installation

```bash
pip install git+https://github.com/nhsx/p24-pvt-diabetes-inequal.git
```

## Workflow

### Initialise Logger
The logging level of `esneft_tools` can be set via the `setVerbosity()` function.

```python
import logging
from esneft_tools.utils import setVerbosity

setVerbosity(logging.INFO)
```

### Retrieve Data from Host
Each of the `esneft_tools.download.getData().fromHost()` functions retrieve a static copy of a particular data set from GitHub.
A local copy of these tables is saved to `./.data-cache/` by default.

  *  `postcodeLSOA`
     * Postcode -> LSOA (2011) lookup Table from [ArcGIS](https://hub.arcgis.com/datasets/6a46e14a6c2441e3ab08c7b277335558/about)
  *  `imdLSOA`
     * Indices of Multiple Deprivation by LSOA in England from [National Statistics (.gov.uk)](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/845345/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv/preview)
  *  `populationLSOA`
    * LSOA population estimates, by age and sex, from [ONS](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimates)
  * `gpRegistration`
    * GP registration by LSOA [NHS Digital](https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice/metadata)
  * `geoLSOA`
    * LSOA GeoJSON from [UK Data Service](https://statistics.ukdataservice.ac.uk/dataset/2011-census-geography-boundaries-lower-layer-super-output-areas-and-data-zones)
  * `esneftLSOA`
    * List of LSOAs within ESNEFT trust.
  * `all` **(default)**
    * Retrieve all of the above data in dictionary format.

```python
from esneft_tools import download

# Instantiate data download class.
getData = download.getData(cache='./.data-cache')

# Retrieve all data as dictionary (recommended)
data = dataDownloader.fromHost('all')

# Alternatively, retrieve  data sets individually
geoLSOA = dataDownloader.fromHost('geoLSOA')
imdLSOA = dataDownloader.fromHost('imdLSOA')
esneftLSOA = dataDownloader.fromHost('esneftLSOA')
postcodeLSOA = dataDownloader.fromHost('postcodeLSOA')
gpRegistration = dataDownloader.fromHost('gpRegistration')
populationLSOA = dataDownloader.fromHost('populationLSOA')
```


## License

Distributed under the MIT License. _See [LICENSE](./LICENSE) for more information._

## Contact

If you have any other questions please contact the author **[Stephen Richer](https://www.linkedin.com/in/stephenricher/)**
at stephen.richer@nhs.net
