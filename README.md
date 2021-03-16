# epfl-enac-it

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

Compute number of average rainy days by month on a given area.

```bash
# run script for data/aoi for the last 20 years (current excluded)
python rainy-days.py data/aoi.shp

# run script for data/aoi with year range [2010, 2020[
python rainy-days.py data/aoi.shp --start 2010 --end 2020

# see help for more options and see defaults
python rainy-days.py -h
```

### Output

Default output folder: ./output

### Pipeline

For each month:

1. Get Image from Google Earth Engine with number of rainy days by year-month
    1. Get ImageCollection from daily CHIRPS
    2. Filter by the year and month
    3. Filter by area of interest
    4. Check if there are any precipitations (> 0), returns 1 else 0
    5. Sum all daily Images to get number of rainy days during the period
2. Loop over all years and compute the mean
3. Get coordinates along with their values given a scale (precision)
4. Put coordinates into a Pandas.DataFrame
5. Pivot the DataFrame with the coordinates to get a matrix of values
6. Convert matrix into integers with rounding (NaN as -1)
7. Save matrix into a raster
    1. Set the geo transform to keep the coordinates
    2. Set nodata to -1 in the metadata for the out of interest area

## raster-viewer

View raster files.

```bash
# install requirements
pip install -r raster-viewer/requirements.txt

# run script
python raster-viewer/main.py

# see help for more options and see defaults
python raster-viewer/main.py -h
```

## Docker

```bash
# build local image
docker build -t rainy-days:latest .

# linux
docker run -it --rm -v $(pwd)/data:/opt/data -v $(pwd)/output:/opt/output rainy-days:latest data/aoi --auth

# cmd
docker run -it --rm -v %cd%\data:/opt/data -v %cd%\output:/opt/output rainy-days:latest data/aoi --auth
```
