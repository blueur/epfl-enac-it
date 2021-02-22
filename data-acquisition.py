import ee
# import shapefile
import geemap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio


def greater_than_zero(image: ee.Image):
    return image.gt(ee.Image.constant(0))


def get_precipitations(scale=1000) -> pd.DataFrame:
    ee.Initialize()
    area = geemap.shp_to_ee("data/aoi.shp")
    image = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
             # .filter(ee.Filter.geometry(area))
             .filter(ee.Filter.date('2020-01-01', '2020-02-01'))
             .map(greater_than_zero)
             .sum())
    image_collection = ee.ImageCollection(image)
    # https://developers.google.com/earth-engine/apidocs/ee-imagecollection-getregion
    region = image_collection.getRegion(geometry=area, scale=scale)
    data = region.getInfo()
    data_frame = pd.DataFrame.from_records(data[1:], columns=data[0])
    print(data_frame)
    return data_frame


def export_raster(array: np.ndarray) -> None:
    profile = rasterio.profiles.DefaultGTiffProfile(count=1)
    print(profile)
    array = array * 8  # FIXME
    with rasterio.open('output.tif', 'w', height=array.shape[0], width=array.shape[1], **profile) as dst:
        dst.write(array.astype(np.uint8), 1)


def show_raster(array: np.ndarray) -> None:
    plt.ion()
    plt.imshow(array)
    plt.ioff()
    plt.show()


def get_grid(data: pd.DataFrame) -> np.ndarray:
    # https://www.hatarilabs.com/ih-en/how-to-create-a-geospatial-raster-from-xy-data-with-python-pandas-and-rasterio-tutorial
    array = (data
             .pivot(index='latitude', columns='longitude', values='precipitation')
             .sort_index(ascending=False))
    print(array)
    return array.to_numpy()


# arr = np.random.randint(30, size=(100,100)).astype(np.uint8)

precipitations = get_precipitations()
grid = get_grid(precipitations)
export_raster(grid)
show_raster(grid)
