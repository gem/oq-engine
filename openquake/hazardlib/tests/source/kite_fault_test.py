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

MAKE_MOVIES = True


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
            profiles = [Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.01, 15.0)]),
                        Line([Point(0.3, 0.0, 0.0), Point(0.3, 0.01, 15.0)])]
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
        self.ruptures = list(source.iter_ruptures())

    def _ruptures_animation(self, surface, ruptures, profiles, first_azi=70):

        # Create the figure
        fig = plt.figure(figsize=(15, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor((0.5, 0.5, 0.5))

        # Plot the fault surface
        mesh = surface.mesh
        x = mesh.lons.flatten()
        y = mesh.lats.flatten()
        z = mesh.depths.flatten()*0.01
        plt.plot(x, y, z, 'o', markersize=1)

        # Plot the first rupture
        x = ruptures[0].surface.mesh.lons.flatten()
        y = ruptures[0].surface.mesh.lats.flatten()
        z = ruptures[0].surface.mesh.depths.flatten()*0.01
        sctt = ax.scatter(x, y, z, marker='s', s=10, c='red')

        fmt = 'Rupture num: {:d} magnitude: {:3.1f}'
        tmp = fmt.format(0, ruptures[0].mag)
        txt = ax.text2D(0.05, 0.95, tmp, transform=ax.transAxes)

        for pro in profiles:
            coo = [(p.longitude, p.latitude, p.depth) for p in pro.points]
            coo = numpy.array(coo)
            plt.plot(coo[:, 0], coo[:, 1], coo[:, 2]*0.01, '--g', lw=3)

        ax.invert_zaxis()

        def animate(i, ruptures, sctt, ax, txt):
            ax.view_init(elev=10., azim=first_azi+i*0.25 % 360)
            x = ruptures[i].surface.mesh.lons.flatten()
            y = ruptures[i].surface.mesh.lats.flatten()
            z = ruptures[i].surface.mesh.depths.flatten()*0.01
            sctt._offsets3d = (x, y, z)
            tmp = fmt.format(i, ruptures[i].mag)
            txt.set_text(tmp)
            return sctt, txt

        anim = animation.FuncAnimation(fig, animate, frames=len(ruptures),
                                       repeat=False,
                                       fargs=(ruptures, sctt, ax, txt),
                                       blit=False, interval=1000)

        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=5, metadata=dict(artist='GEM'),
                        bitrate=1800, extra_args=['-vcodec', 'libx264'])
        anim.save('/tmp/kite_fault_source_test01.mp4', writer=writer)


class SimpleFaultIterRupturesTestCase(_BaseFaultSourceTestCase):

    def aa_test01(self):
        """ Simplest test """
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=6.2, max_mag=6.4,
                             bin_width=0.1)
        source = self._make_source(mfd=mfd, aspect_ratio=1.5)
        self._test_ruptures(None, source)

        if MAKE_MOVIES:
            self._ruptures_animation(source.surface, self.ruptures)

    def test02(self):
        """ Simplest test """

        profiles = [Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.001, 15.0)]),
                    Line([Point(0.1, 0.0, 0.0), Point(0.1, 0.010, 12.0)]),
                    Line([Point(0.2, 0.0, 0.0), Point(0.2, 0.020,  9.0)]),
                    Line([Point(0.3, 0.0, 0.0), Point(0.3, 0.030,  6.0)])]

        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.8, max_mag=6.2,
                             bin_width=0.1)

        source = self._make_source(mfd=mfd, aspect_ratio=1.5,
                                   profiles=profiles)

        self._test_ruptures(None, source)

        if MAKE_MOVIES:
            self._ruptures_animation(source.surface, self.ruptures,
                                     source.profiles)
