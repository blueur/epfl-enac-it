import ee
# import shapefile
import geemap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from scipy.interpolate import griddata


def greater_than_zero(image: ee.Image):
    return image.gt(ee.Image.constant(0))


def get_precipitations():
    ee.Initialize()
    area = geemap.shp_to_ee("data/aoi.shp")
    chirps = ee.ImageCollection(ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
                                .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
                                .map(greater_than_zero)
                                .sum())
    # https://developers.google.com/earth-engine/apidocs/ee-imagecollection-getregion
    data = chirps.getRegion(area, 10000).getInfo()
    data_frame = pd.DataFrame.from_records(data[1:], columns=data[0])
    print(data_frame)
    print(data_frame['precipitation'].max())
    return data_frame


def export_raster(data):
    profile = rasterio.profiles.DefaultGTiffProfile(count=1)
    print(profile)
    data = data * 8  # FIXME
    with rasterio.open('output.tif', 'w', height=data.shape[0], width=data.shape[1], **profile) as dst:
        dst.write(data, 1)


def show_data(data, resolution=0.01):
    # https://www.hatarilabs.com/ih-en/how-to-create-a-geospatial-raster-from-xy-data-with-python-pandas-and-rasterio-tutorial
    points = list(zip(data['longitude'].tolist(), data['latitude'].tolist()))
    values = data['precipitation'].tolist()
    x_range = np.arange(data['longitude'].min(), data['longitude'].max() + resolution, resolution)
    y_range = np.arange(data['latitude'].min(), data['latitude'].max() + resolution, resolution)
    x_grid, y_grid = np.meshgrid(x_range, y_range)
    data_grid = griddata(points, values, (x_grid, y_grid), method='linear')
    plt.ion()
    plt.imshow(data_grid)
    plt.ioff()
    plt.show()


# arr = np.random.randint(30, size=(100,100)).astype(np.uint8)
precipitations = get_precipitations()
show_data(precipitations)
