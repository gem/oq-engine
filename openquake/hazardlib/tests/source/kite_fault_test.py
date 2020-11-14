# The Hazard Library
# Copyright (C) 2012-2020 GEM Foundation
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

import numpy
import unittest
import matplotlib.pyplot as plt

from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D  # This is needed
from openquake.hazardlib.const import TRT
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.tests import assert_pickleable
from openquake.hazardlib.scalerel import PeerMSR, WC1994
from openquake.hazardlib.source.kite_fault import KiteFaultSource
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD

MOVIE = True


class _BaseFaultSourceTestCase(unittest.TestCase):
    TRT = TRT.ACTIVE_SHALLOW_CRUST
    RAKE = 0
    TOM = PoissonTOM(1.)

    def _make_source(self, mfd, aspect_ratio, profiles=None):
        """
        Utility method for creating quickly fault instances
        :param mfd:
        :param aspect_ratio:
        :param profiles:
        """

        # Set the fault source parameter
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        rupture_mesh_spacing = 1.
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        tom = self.TOM
        if profiles is None:
            profiles = [Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.0, 15.0)]),
                        Line([Point(0.3, 0.0, 0.0), Point(0.3, 0.0, 15.0)])]
        floating_x_step = 10.0
        floating_y_step = 5.0

        # Create the source instance
        kfs = KiteFaultSource(source_id, name, trt, mfd, rupture_mesh_spacing,
                              magnitude_scaling_relationship,
                              rupture_aspect_ratio, tom, profiles,
                              floating_x_step, floating_y_step, rake)

        # Check we can create a pickled version of this object
        assert_pickleable(kfs)

        return kfs

    def _test_ruptures(self, expected_ruptures, source):
        ruptures = list(source.iter_ruptures())

    def _ruptures_animation(self, ruptures):

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        plt.style.use('seaborn-bright')


class SimpleFaultIterRupturesTestCase(_BaseFaultSourceTestCase):

    def test01(self):
        """ Simplest test """
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.6, max_mag=6.4,
                             bin_width=0.2)
        source = self._make_source(mfd=mfd, aspect_ratio=1.0)
        # self._test_ruptures(None, computed)

        if MOVIE:
            ruptures = list(source.iter_ruptures())
            self._ruptures_animation(ruptures)

