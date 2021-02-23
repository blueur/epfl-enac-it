import logging
import time
from typing import Tuple

import ee
import numpy as np
import pandas as pd
import rasterio
import shapefile
from affine import Affine
from rasterio.plot import show

CHIRPS_DAILY = 'UCSB-CHG/CHIRPS/DAILY'
NAN_INT = -1

logger = logging.getLogger(__name__)


def greater_than_zero(image: ee.Image):
    return image.gt(ee.Image.constant(0))


def get_area(shp_filename) -> ee.FeatureCollection:
    with shapefile.Reader(shp_filename) as shp:
        return ee.FeatureCollection(shp.__geo_interface__)


def get_precipitations(scale=1000, start='2020-01-01', end='2021-01-01', shp='data/aoi.shp') -> pd.DataFrame:
    ee.Initialize()
    area = get_area(shp)
    image = (ee.ImageCollection(CHIRPS_DAILY)
             .filter(ee.Filter.date(start, end))
             .map(greater_than_zero)
             .sum())
    image_collection = ee.ImageCollection(image)
    # https://developers.google.com/earth-engine/apidocs/ee-imagecollection-getregion
    region = image_collection.getRegion(geometry=area, scale=scale)
    logger.info(f'getting image from {start} to {end}')
    start_time = time.time()
    data = region.getInfo()
    data_frame = pd.DataFrame.from_records(data[1:], columns=data[0])
    logger.info(f'received {data_frame.size:,} coordinates in {time.time() - start_time:0.3f} seconds')
    return data_frame


def export_intarray_to_raster(array: np.ndarray, affine: Affine, filename: str) -> None:
    profile = rasterio.profiles.DefaultGTiffProfile(count=1, dtype=array.dtype)
    height = array.shape[0]
    width = array.shape[1]
    logger.info(f'saving {filename} ({width} x {height}) with profile {profile}')
    with rasterio.open(filename, 'w', height=height, width=width, transform=affine, **profile) as dst:
        dst.write(array, 1)


def export_array_to_raster(array: np.ndarray, affine: Affine, filename: str) -> None:
    array[np.isnan(array)] = NAN_INT
    export_intarray_to_raster(array.astype(np.int8), affine, filename)


def show_raster(filename: str) -> None:
    with rasterio.open(filename) as src:
        show(src)


def get_affine(longitudes: pd.Float64Index, latitudes: pd.Float64Index) -> Affine:
    # https://github.com/sgillies/affine#usage-with-gis-data-packages
    longitude_resolution = (longitudes[-1] - longitudes[0]) / longitudes.size
    latitude_resolution = (latitudes[-1] - latitudes[0]) / latitudes.size
    return Affine.from_gdal(longitudes[0], longitude_resolution, 0.0,
                            latitudes[0], 0.0, latitude_resolution)


def get_array(data: pd.DataFrame) -> Tuple[np.ndarray, Affine]:
    data_frame = (data
                  .pivot(columns='longitude', index='latitude', values='precipitation')
                  .sort_index(ascending=False))
    logger.debug(data_frame)
    affine = get_affine(data_frame.columns, data_frame.index)
    array = data_frame.to_numpy()
    return array, affine


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s:\n%(message)s', level=logging.INFO)
    # logger.setLevel(logging.DEBUG)
    filename = 'output.tif'
    precipitations = get_precipitations()
    array, affine = get_array(precipitations)
    export_array_to_raster(array, affine, filename)
    show_raster(filename)


if __name__ == "__main__":
    main()
