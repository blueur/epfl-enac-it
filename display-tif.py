import argparse
import glob
import os
from typing import List

import rasterio
from rasterio import plot


def display_rasters(filenames: List[str]) -> None:
    for filename in filenames:
        with rasterio.open(filename) as src:
            plot.show(src, title=filename)


def main():
    parser = argparse.ArgumentParser(description='Display raster files.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--output', type=str, default='output',
                        help='output folder')
    args = parser.parse_args()

    display_rasters(glob.glob(os.path.join(args.output, '*.tif')))


if __name__ == "__main__":
    main()
