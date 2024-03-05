#!/usr/bin/env python
# This file is part of 'python-fmask' - a cloud masking module
# Copyright (C) 2015  Neil Flood
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
Functions relating to the creation of a DEM array, using the elevation Python module.

"""
from __future__ import print_function, division

import os
import datetime
import elevation

import numpy
import pyproj
from osgeo import gdal, osr

from rios import applier
from rios import fileinfo


def makeDEMImage(templateimg, outfile, corners, imgInfo):
    """
    Make a single output image file of the DEM for every
    pixel in the template image.

    """
    imgInfo = fileinfo.ImageInfo(templateimg)

    infiles = applier.FilenameAssociations()
    outfiles = applier.FilenameAssociations()
    otherargs = applier.OtherInputs()
    controls = applier.ApplierControls()

    infiles.img = templateimg
    outfiles.dem = outfile

    otherargs.xMin = imgInfo.xMin
    otherargs.xMax = imgInfo.xMax
    otherargs.yMin = imgInfo.yMin
    otherargs.yMax = imgInfo.yMax
    otherargs.proj = imgInfo.projection
    otherargs.transform = imgInfo.transform
    otherargs.file = templateimg
    controls.setStatsIgnore(500)

    applier.apply(makeDEM, infiles, outfiles, otherargs, controls=controls)


def makeDEM(info, inputs, outputs, otherargs):
    """
    Called from RIOS

    Make DEM file for same extent as template image

    """
    # Extract corners
    (xMin, xMax, yMin, yMax) = (otherargs.xMin, otherargs.xMax, otherargs.yMin, otherargs.yMax)

    # Convert to lat/lon
    p1 = pyproj.Proj(otherargs.proj, preserve_units=True)
    (LonMin, LatMin) = p1(xMin, yMin, inverse=True)
    (LonMax, LatMax) = p1(xMax, yMax, inverse=True)
    print("Extracting DEM for: {:.3f}:{:.3f} {:.3f}:{:.3f}".format(LonMin, LonMax, LatMin, LatMax))

    # clip the SRTM1 30m DEM and save it to a temp tif file
    tempdem = os.path.join(os.path.dirname(otherargs.file), 'DEM_SRTM.tif')
    if os.path.exists(tempdem):
        os.remove(tempdem)
    # 'left bottom right top' order
    elevation.clip(bounds=(LonMin, LatMin, LonMax, LatMax), product='SRTM3', output=tempdem)
    # clean up stale temporary files and fix the cache in the event of a server error
    elevation.clean()

    # Load temptif into numpy array
    ds = gdal.Open(tempdem, gdal.GA_ReadOnly)
    rb = ds.GetRasterBand(1)
    dem = rb.ReadAsArray()
    ds = None
    #print("{} DEM: {} {}".format(inputs.img.shape,numpy.nanmin(dem), numpy.nanmax(dem)))

    # Save in output file
    (xblock, yblock) = info.getBlockCoordArrays()
    img_array = numpy.zeros(xblock.shape)
    img_array[:, :] = -32768
    #print("{} Geotransform: {}".format(xblock.shape,otherargs.transform))
    # GeoTIFF Geotransform
    xoff, a, b, yoff, d, e = otherargs.transform
    xp = (xblock - xoff) / a
    yp = (yblock - yoff) / e
    # Map array
    xdim,ydim = img_array.shape
    count = 0
    for i in range(xdim):
        for j in range(ydim):
            #print(i,j,xblock[i,j],yblock[i,j],xp[i,j],yp[i,j])
            xval,yval = int(xp[i,j]),int(yp[i,j])
            if xval>= 0 and yval >= 0 and xval<xdim and yval<ydim:
                img_array[i,j] = dem[xval,yval]
                count += 1

    print("{} vals DEM: {} {}".format(count,numpy.nanmin(img_array), numpy.nanmax(img_array)))

    img_array = numpy.expand_dims(img_array, axis=0)  # convert single layer to 3d array
    outputs.dem = img_array
