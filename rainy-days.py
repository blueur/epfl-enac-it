import argparse
import logging
import os
import time
from datetime import datetime
from typing import Tuple, List

import ee
import numpy as np
import pandas as pd
import rasterio
import shapefile
from affine import Affine
from dateutil.relativedelta import relativedelta

CHIRPS_DAILY = 'UCSB-CHG/CHIRPS/DAILY'
NAN_INT = -1
YEAR_MONTH_FORMAT = '%Y-%m'
YEAR_MONTH_DAY_FORMAT = f'{YEAR_MONTH_FORMAT}-%d'

logger = logging.getLogger(__name__)


def greater_than_zero(image: ee.Image):
    return image.gt(ee.Image.constant(0))


def get_area(shp_filename) -> ee.FeatureCollection:
    with shapefile.Reader(shp_filename) as shp:
        return ee.FeatureCollection(shp.__geo_interface__)


def get_precipitations(shp: str, scale, start: str, end: str) -> pd.DataFrame:
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


def get_monthly_precipitations(shp: str, scale, year_month: pd.Period) -> pd.DataFrame:
    timestamp = year_month.to_timestamp(how='S')
    start = timestamp.strftime(YEAR_MONTH_DAY_FORMAT)
    end = (timestamp + pd.DateOffset(months=1)).strftime(YEAR_MONTH_DAY_FORMAT)
    return get_precipitations(shp=shp, scale=scale, start=start, end=end)


def export_intarray_to_raster(array: np.ndarray, affine: Affine, filename: str) -> str:
    profile = rasterio.profiles.DefaultGTiffProfile(count=1, dtype=array.dtype)
    height = array.shape[0]
    width = array.shape[1]
    logger.info(f'saving {filename} ({width} x {height})')
    with rasterio.open(filename, 'w', height=height, width=width, transform=affine, **profile) as dst:
        dst.write(array, 1)
    return filename


def export_array_to_raster(array: np.ndarray, affine: Affine, filename: str) -> str:
    array[np.isnan(array)] = NAN_INT
    return export_intarray_to_raster(array.astype(np.int8), affine, filename)


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


def get_year_months(start: str, end: str) -> List[pd.Period]:
    return pd.period_range(start=start, end=end, freq='M')[:-1]


def compute_monthly(shp: str, scale: int, start: str, end: str, output: str):
    for year_month in get_year_months(start=start, end=end):
        filename = os.path.join(output, f'{year_month.strftime(YEAR_MONTH_FORMAT)}.tif')
        precipitations = get_monthly_precipitations(shp=shp, scale=scale, year_month=year_month)
        array, affine = get_array(precipitations)
        export_array_to_raster(array, affine, filename)


def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s', level=logging.INFO)
    datetime_now = datetime.now()

    parser = argparse.ArgumentParser(description='compute number of monthly rainy days on a given area',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('shp', type=str,
                        help='shapefile location')
    parser.add_argument('--scale', type=int, default=1000,
                        help='scale in meters')
    parser.add_argument('--output', type=str, default='output',
                        help='output folder')
    parser.add_argument('--start', type=str,
                        default=(datetime_now - relativedelta(years=1)).strftime(YEAR_MONTH_FORMAT),
                        help='included starting month (YYYY-MM)')
    parser.add_argument('--end', type=str, default=datetime_now.strftime(YEAR_MONTH_FORMAT),
                        help='excluded ending month (YYYY-MM)')
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction,
                        help='activate debug logs')

    args = parser.parse_args()
    logger.info(f'args: {args.__dict__}')
    if args.debug:
        logger.setLevel(logging.DEBUG)

    os.makedirs(args.output, exist_ok=True)
    datetime.strptime(args.start, YEAR_MONTH_FORMAT)
    datetime.strptime(args.end, YEAR_MONTH_FORMAT)

    compute_monthly(shp=args.shp,
                    scale=args.scale,
                    start=args.start,
                    end=args.end,
                    output=args.output)


if __name__ == "__main__":
    main()
