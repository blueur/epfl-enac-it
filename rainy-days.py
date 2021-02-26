import argparse
import logging
import os
import time
from datetime import datetime
from typing import Tuple

import ee
import numpy as np
import pandas as pd
import rasterio
import shapefile
from affine import Affine
from dateutil.relativedelta import relativedelta

CHIRPS_DAILY = 'UCSB-CHG/CHIRPS/DAILY'
NAN_INT = -1

logger = logging.getLogger(__name__)


def greater_than_zero(image: ee.Image) -> ee.Image:
    return image.gt(ee.Image.constant(0))


def get_area(shp_filename: str) -> ee.FeatureCollection:
    with shapefile.Reader(shp_filename) as shp:
        return ee.FeatureCollection(shp.__geo_interface__)


def get_monthly_precipitations(area: ee.FeatureCollection, scale: int, month: int,
                               start_year: int, end_year: int) -> pd.DataFrame:
    # https://developers.google.com/earth-engine/apidocs/ee-filter-calendarrange
    images = [(ee.ImageCollection(CHIRPS_DAILY)
               .filter(ee.Filter.calendarRange(month, month, 'month'))
               .filter(ee.Filter.calendarRange(year, year, 'year'))
               .map(greater_than_zero)
               .sum()) for year in range(start_year, end_year)]
    image = ee.ImageCollection.fromImages(images).mean()
    image_collection = ee.ImageCollection(image)
    # https://developers.google.com/earth-engine/apidocs/ee-imagecollection-getregion
    region = image_collection.getRegion(geometry=area, scale=scale)
    logger.info(f'getting image in year range [{start_year}, {end_year}[ with month {month}/12')
    start_time = time.time()
    data = region.getInfo()
    data_frame = pd.DataFrame.from_records(data[1:], columns=data[0])
    logger.info(f'received {data_frame.size:,} coordinates in {time.time() - start_time:0.3f} seconds')
    return data_frame


def export_intarray_to_raster(array: np.ndarray, affine: Affine, filename: str) -> str:
    profile = rasterio.profiles.DefaultGTiffProfile(count=1, dtype=array.dtype, nodata=NAN_INT)
    height = array.shape[0]
    width = array.shape[1]
    logger.info(f'saving {filename} ({width} x {height})')
    with rasterio.open(filename, 'w', height=height, width=width, transform=affine, **profile) as dst:
        dst.write(array, 1)
    return filename


def export_array_to_raster(array: np.ndarray, affine: Affine, filename: str) -> str:
    array[np.isnan(array)] = NAN_INT
    intarray = np.around(array).astype(np.int8)
    return export_intarray_to_raster(intarray, affine, filename)


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


def compute_monthly(shp: str, scale: int, start_year: int, end_year: int, output: str):
    area = get_area(shp)
    for month in range(1, 13):
        filename = os.path.join(output, f'{month:02d}.tif')
        precipitations = get_monthly_precipitations(area=area, scale=scale, month=month,
                                                    start_year=start_year, end_year=end_year)
        array, affine = get_array(precipitations)
        export_array_to_raster(array, affine, filename)


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', level=logging.INFO)
    datetime_now = datetime.now()

    parser = argparse.ArgumentParser(description='Compute number of average rainy days by month on a given area.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('shp', type=str,
                        help='shapefile location')
    parser.add_argument('--scale', type=int,
                        default=1000,
                        help='scale in meters')
    parser.add_argument('--output', type=str,
                        default='output',
                        help='output folder')
    parser.add_argument('--start', type=int,
                        default=(datetime_now - relativedelta(years=20)).year,
                        help='included starting year')
    parser.add_argument('--end', type=int,
                        default=datetime_now.year,
                        help='excluded ending year')
    parser.add_argument('--auth', action=argparse.BooleanOptionalAction,
                        default=False,
                        help='Google Earth Engine authentication')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction,
                        default=False,
                        help='activate debug logs')

    args = parser.parse_args()
    logger.info(f'args: {args.__dict__}')
    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.auth:
        ee.Authenticate()
    ee.Initialize()
    os.makedirs(args.output, exist_ok=True)

    compute_monthly(shp=args.shp,
                    scale=args.scale,
                    start_year=args.start,
                    end_year=args.end,
                    output=args.output)


if __name__ == "__main__":
    main()
