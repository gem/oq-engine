# The Hazard Library
# Copyright (C) 2014-2026 GEM Foundation
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
    mblg_to_mw_johnston_96, mblg_to_mw_atkinson_boore_87, clip_mean)
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib import gsim, InvalidFile
from openquake.pfd.registry import SLOTS, get_available

GSIM_PATH = gsim.__path__[0]
SUMMARY = os.path.normpath(
    os.path.join(
        GSIM_PATH, '../../../doc/api-reference/openquake.hazardlib.gsim.rst'))
PFD_SUMMARY = os.path.normpath(os.path.join(
    GSIM_PATH, '../../../doc/user-guide/advanced/'
    'probabilistic-fault-displacement.rst'))
PFD_API_SUMMARY = os.path.normpath(os.path.join(
    GSIM_PATH, '../../../doc/api-reference/openquake.pfd.rst'))
PFD_API_DIR = os.path.normpath(os.path.join(
    GSIM_PATH, '../../../doc/api-reference/pfd-models'))


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
    """Check that GSIM modules and PFD models are documented."""
    def test_documented(self):
        txt = open(SUMMARY).read()
        for name in os.listdir(GSIM_PATH):
            if name.endswith('.py') and not name.startswith('_'):
                if name[:-3] not in txt:
                    raise InvalidFile('%s: %s is not documented' %
                                      (SUMMARY, name))

    def test_pfd_models_documented(self):
        txt = open(PFD_SUMMARY).read()
        names = sorted({name for slot in SLOTS
                        for name in get_available(slot)})
        missing = [name for name in names if name not in txt]
        if missing:
            raise InvalidFile('%s: PFD models are not documented: %s' %
                              (PFD_SUMMARY, ', '.join(missing)))

    def test_pfd_models_in_api_reference(self):
        index = open(PFD_API_SUMMARY).read()
        missing = []
        for slot in SLOTS:
            page = os.path.join(PFD_API_DIR, slot + '.rst')
            if slot not in index or not os.path.isfile(page):
                missing.extend(get_available(slot))
                continue
            slot_txt = open(page).read()
            for name, cls in get_available(slot).items():
                directive = '.. autoclass:: %s.%s' % (cls.__module__, name)
                if directive not in slot_txt:
                    missing.append(name)
        if missing:
            raise InvalidFile('%s: PFD models are not documented: %s' %
                              (PFD_API_SUMMARY, ', '.join(missing)))
