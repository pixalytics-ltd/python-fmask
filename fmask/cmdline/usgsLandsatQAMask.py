# This file is part of 'python-fmask' - a cloud masking module
# Copyright (C) 2024  Sam Lavender
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
from __future__ import print_function, division

import sys
import argparse
from fmask import qabandcheck
from fmask import config


def getCmdargs():
    """
    Get command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile', help='Input QA band image')
    parser.add_argument('-m', '--mtl', help='.MTL  file')
    parser.add_argument('-o', '--output', help='Output QA mask file')

    cmdargs = parser.parse_args()

    if (cmdargs.infile is None or cmdargs.mtl is None or  
            cmdargs.output is None):
        parser.print_help()
        sys.exit()
    
    return cmdargs


def mainRoutine():
    cmdargs = getCmdargs()

    makeQAMask(cmdargs.mtl, cmdargs.infile, cmdargs.output)


def makeQAMask(mtlfile, infile, outfile):
    """
    Callable main routine
    """
    mtlInfo = config.readMTLFile(mtlfile)
    landsat = mtlInfo['SPACECRAFT_ID'][-1]
    sensor = mtlInfo['SENSOR_ID']
    
    if sensor == 'MSS':
        sensor = config.FMASK_LANDSATMSS
    elif landsat == '4':
        sensor = config.FMASK_LANDSAT47
    elif landsat == '5':
        sensor = config.FMASK_LANDSAT47
    elif landsat == '7':
        sensor = config.FMASK_LANDSAT47
    elif landsat in ('8', '9'):
        sensor = config.FMASK_LANDSATOLI
    else:
        raise SystemExit('Unsupported Landsat sensor')

    # needed so the saturation function knows which
    # bands are visible etc.
    fmaskConfig = config.FmaskConfig(sensor)
    
    qabandcheck.makeQAMask(fmaskConfig, infile, outfile)

