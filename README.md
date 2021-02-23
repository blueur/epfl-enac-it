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

### Pipeline

For each month:

1. Get Image from Google Earth Engine with number of rainy days
    1. Get ImageCollection from daily CHIRPS
    2. Filter by the year and month
    3. Filter by area of interest
    4. Check if there are any precipitations (> 0), returns 1 else 0
    5. Sum all daily Images to get number of rainy days during the period
    6. Loop over all years on the same month and compute the mean
2. Get coordinates along with their values given a scale (precision)
3. Put coordinates into a Pandas.DataFrame
4. Pivot the DataFrame with the coordinates to get a matrix of values
5. Convert matrix into integers with rounding (NaN as -1)
6. Save matrix into a raster
    1. Set the geo transform to keep the coordinates
    2. Set nodata to -1 in the metadata for the out of interest area

## raster-viewer

View raster files.

```bash
# run script
python raster-viewer.py

# see help for more options and see defaults
python raster-viewer.py -h
```

## Docker

```bash
docker build -t rainy-days:latest .
docker run -it --rm -v D:\git\epfl-enac\data:/opt/data -v D:\git\epfl-enac\output:/opt/output rainy-days:latest python rainy-days.py data/aoi --auth
```
