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


    # clip the SRTM1 30m DEM and save it to a temp tif file
    temp = os.path.join(os.path.dirname(otherargs.file), 'temp.tif')
    tempdem = os.path.join(os.path.dirname(otherargs.file), 'DEM_SRTM.tif')
    if not os.path.exists(tempdem):
        # Convert to lat/lon
        p1 = pyproj.Proj(otherargs.proj, preserve_units=True)
        (LonMin, LatMin) = p1(xMin, yMin, inverse=True)
        (LonMax, LatMax) = p1(xMax, yMax, inverse=True)

        print("Extracting SRTM DEM for: {:.3f}:{:.3f} {:.3f}:{:.3f}".format(LonMin, LonMax, LatMin, LatMax))
        # 'left bottom right top' order, buffer to ensure full scene is captured
        buffer=0.2
        elevation.clip(bounds=(LonMin-buffer, LatMin-buffer, LonMax+buffer, LatMax+buffer), product='SRTM3', output=temp)
        # clean up stale temporary files and fix the cache in the event of a server error
        elevation.clean()

        # reproject to same projection as Landsat
        sr = osr.SpatialReference(wkt=otherargs.proj)
        epsg_code = r"{}".format(sr.GetAttrValue('AUTHORITY', 1))
        print("Projection: {}".format(epsg_code))
        warp = gdal.Warp(tempdem, temp, dstSRS='EPSG:{}'.format(epsg_code))
        warp = None  # Closes the files
        os.remove(temp)

    # Load tempdem into numpy array
    ds = gdal.Open(tempdem, gdal.GA_ReadOnly)

    # Extract geotransform
    geoTransform = ds.GetGeoTransform()

    # Extract image
    rb = ds.GetRasterBand(1)
    dem = rb.ReadAsArray()
    ds = None

    # Save in output file
    (xblock, yblock) = info.getBlockCoordArrays()
    img_array = numpy.zeros(xblock.shape)
    img_array[:, :] = -32768
    # GeoTIFF Geotransform
    #print("{} Geotransform: {}".format(xblock.shape,geoTransform))
    xoff, a, b, yoff, d, e = geoTransform
    xp = (xblock - xoff) / a
    yp = (yblock - yoff) / e
    # Map array
    ydim,xdim = img_array.shape
    count = 0
    for i in range(ydim):
        for j in range(xdim):
            xval,yval = int(numpy.floor(xp[i,j])),int(numpy.floor(yp[i,j]))
            if xval>= 0 and yval >= 0 and yval<dem.shape[0] and xval<dem.shape[1]:
                img_array[i,j] = dem[yval,xval]
                count += 1
            #else:
            #    print(img_array.shape,dem.shape,i,j,yblock[i,j],xblock[i,j],yp[i,j],xp[i,j],yval,xval)
            #    stop


    #print("{} of {} vals DEM: {} {}\n".format(count,xdim*ydim,numpy.nanmin(img_array), numpy.nanmax(img_array)))
    img_array = numpy.expand_dims(img_array, axis=0)  # convert single layer to 3d array
    outputs.dem = img_array
