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
Generate an output image file with dem values.

"""
from __future__ import print_function, division

import sys
import argparse

from fmask import landsatangles, landsatdem
from fmask import config

from rios import fileinfo


def getCmdargs():
    """
    Get commandline arguments
    """
    p = argparse.ArgumentParser()
    p.add_argument("-m", "--mtl", help="MTL text file of USGS metadata")
    p.add_argument("-t", "--templateimg", 
        help="Image filename to use as template for output angles image")
    p.add_argument("-o", "--outfile", help="Output image file")
    cmdargs = p.parse_args()
    if (cmdargs.mtl is None or cmdargs.templateimg is None or 
            cmdargs.outfile is None):
        p.print_help()
        sys.exit(1)
    return cmdargs


def mainRoutine():
    """
    Main routine
    """
    cmdargs = getCmdargs()

    makeDEM(cmdargs.mtl, cmdargs.templateimg, cmdargs.outfile)


def makeDEM(mtlfile, templateimg, outfile):
    """
    Callable main routine
    """
    mtlInfo = config.readMTLFile(mtlfile)
    
    imgInfo = fileinfo.ImageInfo(templateimg)
    corners = landsatangles.findImgCorners(templateimg, imgInfo)

    landsatdem.makeDEMImage(templateimg, outfile, corners, imgInfo)
