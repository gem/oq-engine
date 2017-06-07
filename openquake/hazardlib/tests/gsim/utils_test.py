# The Hazard Library
# Copyright (C) 2014-2017 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os
import numpy

from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_johnston_96, mblg_to_mw_atkinson_boore_87, clip_mean
)
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib import gsim, InvalidFile

GSIM_PATH = gsim.__path__[0]
SUMMARY = os.path.normpath(
    os.path.join(
        GSIM_PATH, '../../../doc/sphinx/openquake.hazardlib.gsim.rst'))


class MblgToMwTestCase(unittest.TestCase):
    def test_mblg_to_mw_johnston_96(self):
        mblg = 5
        mw = mblg_to_mw_johnston_96(mblg)
        self.assertAlmostEqual(mw, 4.6725)

    def test_mblg_to_mw_atkinson_boore_87(self):
        mblg = 5
        mw = mblg_to_mw_atkinson_boore_87(mblg)
        self.assertAlmostEqual(mw, 4.5050)


class ClipMeanTestCase(unittest.TestCase):
    def test_clip_mean(self):
        mean = numpy.array([0.1, 0.2, 0.6, 1.2])
        imt = PGA()
        clipped_mean = clip_mean(imt, mean)

        numpy.testing.assert_allclose(
            [0.1, 0.2, 0.405, 0.405], clipped_mean
        )

        mean = numpy.array([0.1, 0.2, 0.6, 1.2])
        imt = SA(period=0.1, damping=5.)
        clipped_mean = clip_mean(imt, mean)

        numpy.testing.assert_allclose(
            [0.1, 0.2, 0.6, 1.099], clipped_mean
        )

        mean = numpy.array([0.1, 0.2, 0.6, 1.2])
        imt = SA(period=0.6, damping=5.)
        clipped_mean = clip_mean(imt, mean)

        numpy.testing.assert_allclose(
            [0.1, 0.2, 0.6, 1.2], clipped_mean
        )

        mean = numpy.array([0.1, 0.2, 0.6, 1.2])
        imt = SA(period=0.01, damping=5.)
        clipped_mean = clip_mean(imt, mean)

        numpy.testing.assert_allclose(
            [0.1, 0.2, 0.6, 1.2], clipped_mean
        )


class DocumentationTestCase(unittest.TestCase):
    """Make sure each GSIM module is listed in openquake.hazardlib.gsim.rst"""
    def test_documented(self):
        txt = open(SUMMARY).read()
        for name in os.listdir(GSIM_PATH):
            if name.endswith('.py') and not name.startswith('_'):
                if name[:-3] not in txt:
                    raise InvalidFile('%s: %s is not documented' %
                                      (SUMMARY, name))
