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


### Retrieve Data
Each of the `esneft_tools.download.get*()` functions retrieve a static copy of a particular data set from GitHub.
A local copy of these tables is saved to `{dir}/.esneft_cache/`.
By default `dir` is set to `./` (the current directory) but this can be modified through the function arguments.

  *  `getLookup()`
     * Postcode -> LSOA (2011) Lookup Table from [ArcGIS](https://hub.arcgis.com/datasets/6a46e14a6c2441e3ab08c7b277335558/about)
  *  `getDeprivation()`
     * Indices of Multiple Deprivation by LSOA in England from [National Statistics (.gov.uk)](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/845345/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv/preview)
  * `getPopulation()`
    * LSOA population estimates, by age and sex, from [ONS](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimates)

```python
from esneft_tools.download import getLookup, getIMD

lookup = getLookup()

# Full list of Multiple Deprivation Indices
imd = getIMD()

# Population estimates by LSOA level
popSummary, popMedian = getPopulation()
```




## License

Distributed under the MIT License. _See [LICENSE](./LICENSE) for more information._

## Contact

If you have any other questions please contact the author **[Stephen Richer](https://www.linkedin.com/in/stephenricher/)**
at stephen.richer@nhs.net
