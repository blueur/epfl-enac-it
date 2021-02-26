import argparse
import glob
import math
import os
from typing import List

import matplotlib.pyplot as plt
import rasterio
from rasterio import plot


def view_raster_files(filenames: List[str], ncols: int) -> None:
    nrows = math.ceil(len(filenames) / ncols)
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, num=len(filenames))
    flat_axes = [ax for sub_axes in axes for ax in sub_axes]
    plt.ion()
    for i, filename in enumerate(filenames):
        with rasterio.open(filename) as src:
            plot.show(src, title=extract_title(filename), ax=flat_axes[i])
    for ax in flat_axes[len(filenames):]:
        ax.set_visible(False)
    plt.ioff()
    plt.show()


def extract_title(filename):
    return os.path.splitext(os.path.split(filename)[-1])[0]


def main():
    parser = argparse.ArgumentParser(description='View raster files.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--output', type=str, default='output',
                        help='output folder')
    parser.add_argument('--ncols', type=int, default=4,
                        help='number of columns')
    args = parser.parse_args()

    view_raster_files(glob.glob(os.path.join(args.output, '*.tif')), args.ncols)


if __name__ == "__main__":
    main()
