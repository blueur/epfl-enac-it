# epfl-enac

## Installation

Requirement:

* Python 3.9+ with pip

```bash
pip install -r requirements.txt
# or 
conda install --file requirements.txt
```

### Windows

Follow https://rasterio.readthedocs.io/en/latest/installation.html#windows
to install rasterio with conda or from binaries.

## rainy-days

Compute number of monthly rainy days on a given area.

```bash
# run script for data/aoi
python rainy-days.py data/aoi.shp

# see help for more options and see defaults
python rainy-days.py -h
```

### Output

Default output folder: ./output

## raster-viewer

View raster files.

```bash
# run script
python raster-viewer.py

# see help for more options and see defaults
python raster-viewer.py -h
```
