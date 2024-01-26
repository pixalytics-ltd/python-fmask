"""
Module for doing checks of the QA band to remove spurious pixels from the mask.
"""

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

import numpy
from rios import applier, cuiprogress
from . import config


def makeQAMask(fmaskConfig, QAFile, outMask):
    """
    Checks the QA Band File and creates a mask with
    1's where there is a known issue, 0 otherwise.
    
    The format of outMask will be the current
    RIOS default format.

    """
    inputs = applier.FilenameAssociations()
    inputs.qa = QAFile
    
    outputs = applier.FilenameAssociations()
    outputs.mask = outMask
    
    otherargs = applier.OtherInputs()
    otherargs.esa = fmaskConfig.esa

    controls = applier.ApplierControls()
    controls.progress = cuiprogress.GDALProgressBar()
    
    applier.apply(riosQAMask, inputs, outputs,
                otherargs, controls=controls)


def find_bits(arr, b1, b2):
    width_int = int((b1 - b2 + 1) * "1", 2)
    return ((arr >> b2) & width_int).astype('uint8')


def riosQAMask(info, inputs, outputs, otherargs):
    """
    Called from RIOS. Does the actual QA test.
    
    """
    # Setup zero array
    outShape = inputs.qa.shape
    outputs.mask = numpy.zeros(outShape, dtype=numpy.uint8)

    # Set mask for any flagged issues
    # See https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands

    ## Dropped pixels
    mask = find_bits(inputs.qa, 9, 9)
    outputs.mask[mask == 1] = 1

