# The Hazard Library
# Copyright (C) 2012-2023 GEM Foundation
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

from openquake.hazardlib.const import TRT
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.tests import assert_pickleable
from openquake.hazardlib.scalerel import PeerMSR
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.source.kite_fault import KiteFaultSource
from openquake.hazardlib.mfd import TruncatedGRMFD
from openquake.hazardlib.tests.geo.surface.kite_fault_test import ppp

# Movies are in /tmp
MAKE_MOVIES = False
MAKE_PICTURES = False


class _BaseFaultSourceTestCase(unittest.TestCase):
    TRT = TRT.ACTIVE_SHALLOW_CRUST
    RAKE = 0
    TOM = PoissonTOM(1.)

    def _make_source(self, mfd, aspect_ratio, profiles=None,
                     floating_x_step=0.5, floating_y_step=0.5):
        """
        Utility method for creating quickly fault instances
        :param mfd:
            An instance of :class:`openquake.hazardlib.scalerel.base.`
        :param aspect_ratio:
            The rupture aspect ratio
        :param profiles:
            A list of profiles used to build the fault surface
        """

        # Set the fault source parameter
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        rupture_mesh_spacing = 2.5
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = aspect_ratio
        tom = self.TOM
        if profiles is None:
            profiles = [Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.01, 15.0)]),
                        Line([Point(0.3, 0.0, 0.0), Point(0.3, 0.01, 15.0)])]

        # Create the source instance
        kfs = KiteFaultSource(source_id, name, trt, mfd, rupture_mesh_spacing,
                              magnitude_scaling_relationship,
                              rupture_aspect_ratio, tom, profiles, rake,
                              floating_x_step=floating_x_step,
                              floating_y_step=floating_y_step)

        # Check we can create a pickled version of this object
        assert_pickleable(kfs)
        return kfs

    def _ruptures_animation(self, lab, surface, ruptures, profiles,
                            first_azi=70):

        # Create the figure
        fig = plt.figure(figsize=(15, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor((0.5, 0.5, 0.5))

        # Plot the fault surface
        mesh = surface.mesh
        x = mesh.lons.flatten()
        y = mesh.lats.flatten()
        z = mesh.depths.flatten() * 0.01
        plt.plot(x, y, z, 'o', markersize=1)

        # Plot the first rupture
        x = ruptures[0].surface.mesh.lons.flatten()
        y = ruptures[0].surface.mesh.lats.flatten()
        z = ruptures[0].surface.mesh.depths.flatten() * 0.01
        sctt = ax.scatter(x, y, z, marker='s', s=10, c='red')

        fmt = 'Rupture num: {:d} magnitude: {:3.1f}'
        tmp = fmt.format(0, ruptures[0].mag)
        txt = ax.text2D(0.05, 0.95, tmp, transform=ax.transAxes)

        for pro in profiles:
            coo = [(p.longitude, p.latitude, p.depth) for p in pro.points]
            coo = numpy.array(coo)
            plt.plot(coo[:, 0], coo[:, 1], coo[:, 2] * 0.01, '--g', lw=3)

        ax.invert_zaxis()

        def animate(i, ruptures, sctt, ax, txt):
            ax.view_init(elev=10., azim=(first_azi + i * 0.25) % 360)
            x = ruptures[i].surface.mesh.lons.flatten()
            y = ruptures[i].surface.mesh.lats.flatten()
            z = ruptures[i].surface.mesh.depths.flatten() * 0.01
            sctt._offsets3d = (x, y, z)
            tmp = fmt.format(i, ruptures[i].mag)
            txt.set_text(tmp)
            return sctt, txt

        anim = animation.FuncAnimation(fig, animate, frames=len(ruptures),
                                       repeat=False,
                                       fargs=(ruptures, sctt, ax, txt),
                                       blit=False, interval=1000)

        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=2, metadata=dict(artist='GEM'),
                        bitrate=1800, extra_args=['-vcodec', 'libx264'])
        fname = '/tmp/kite_fault_source_{:s}.mp4'.format(lab)
        anim.save(fname, writer=writer)

        fname = '/tmp/kite_fault_source_{:s}.html'.format(lab)
        with open(fname, "w") as f:
            print(anim.to_html5_video(), file=f)


class FromSimpleFaultDataTestCase(unittest.TestCase):
    TRT = TRT.ACTIVE_SHALLOW_CRUST
    RAKE = 0
    TOM = PoissonTOM(1.)

    def test01(self):
        source_id = name = 'test-source'
        trt = self.TRT
        rake = self.RAKE
        rupture_mesh_spacing = 2.5
        upper_seismogenic_depth = 0
        lower_seismogenic_depth = 4.2426406871192848
        magnitude_scaling_relationship = PeerMSR()
        rupture_aspect_ratio = 2.0
        tom = self.TOM
        fault_trace = Line([Point(0.0, 0.0),
                            Point(0.0, 0.0359728811758),
                            Point(0.0190775080917, 0.0550503815181),
                            Point(0.03974514139, 0.0723925718855)])
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.8, max_mag=6.2,
                             bin_width=0.1)
        floating_x_step = 0.5
        floating_y_step = 0.5
        dip = 90.0
        src = KiteFaultSource.as_simple_fault(
            source_id, name, trt, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            tom, upper_seismogenic_depth,
            lower_seismogenic_depth, fault_trace, dip, rake,
            floating_x_step, floating_y_step)

        sfs = SimpleFaultSurface.from_fault_data(fault_trace,
                                                 upper_seismogenic_depth,
                                                 lower_seismogenic_depth,
                                                 dip, rupture_mesh_spacing)

        msh = Mesh(lons=numpy.array([0.02]), lats=numpy.array([0.03]),
                   depths=numpy.array([0.0]))

        rrup_sf = sfs.get_min_distance(msh)
        rrup_kf = src.surface.get_min_distance(msh)
        numpy.testing.assert_almost_equal(rrup_sf, rrup_kf, decimal=1)

        if MAKE_PICTURES:
            ppp(src.profiles, src.surface)


class SimpleFaultIterRupturesTestCase(_BaseFaultSourceTestCase):

    def test01(self):
        """ Simplest surface, 0.5 floating (half overlap). The sampler
        decreases the number of nodes on the mesh surface that are skipped
        such that the ruptures can be equally spaced"""

        # Create the magnitude-frequency distribution
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=6.2, max_mag=6.4,
                             bin_width=0.1)
        source = self._make_source(mfd=mfd, aspect_ratio=1.5)

        # The fault surface created should contain 13 quadrilaterals along
        # the strike and 9 quadrilaterals along the dip. The distance between
        # the two profiles is 33 km. Given that we use a grid spacing of
        # 2.5 km, 2.5 * 13 gives 32.5 km. The grid spacing along dip is scaled
        # by the aspect ratio so that the sampling is proportional along
        # strike and dip. In this case the sampling along strike is 1.66km

        msg = 'Wrong surface mesh'
        self.assertEqual(source.surface.mesh.lons.shape[1], 14, msg)
        self.assertEqual(source.surface.mesh.lons.shape[0], 10, msg)

        # Regarding ruptures, the lowest magnitude admitted by the MFD is 6.25
        # hence - given that the corresponding area of the rupture is 178 km
        # and the aspect ratio is 1.5 the mesh covered by this rupture must
        # have the following dimensions:
        # - width = 10.68 km i.e. 6 quadrilaterals and 7 vertexes
        # - lenght = 16.02 km i.e. 7 quadrilaterals and 8 vertexes

        for idx, tmp in enumerate(source.iter_ruptures()):
            rup = tmp
            if idx == 0:
                break

        msg = 'Wrong dimension of the rupture'
        self.assertEqual(rup.surface.mesh.lons.shape[0], 7, msg)
        self.assertEqual(rup.surface.mesh.lons.shape[1], 8, msg)

        msg = 'Wrong number of ruptures'
        self.assertEqual(source.count_ruptures(), 12, msg)

        if MAKE_PICTURES:
            ppp(source.profiles, source.surface)

        if MAKE_MOVIES:
            ruptures = [r for r in source.iter_ruptures()]
            self._ruptures_animation('test01', source.surface, ruptures,
                                     source.profiles)

    def test02(self):
        """ Increases the complexity of the surface; because of the surface
        geometry, the floating factor only impacts the along-strike sampling
        and only for some magnitudes """

        profiles = [Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.001, 15.0)]),
                    Line([Point(0.1, 0.0, 0.0), Point(0.1, 0.010, 12.0)]),
                    Line([Point(0.2, 0.0, 0.0), Point(0.2, 0.020,  9.0)]),
                    Line([Point(0.3, 0.0, 0.0), Point(0.3, 0.030,  6.0)])]

        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.8, max_mag=6.2,
                             bin_width=0.1)

        source = self._make_source(mfd=mfd, aspect_ratio=1.5,
                                   profiles=profiles)

        if MAKE_MOVIES:
            ruptures = [r for r in source.iter_ruptures()]
            self._ruptures_animation('test02', source.surface, ruptures,
                                     source.profiles)

        msg = 'Wrong number of ruptures'
        self.assertEqual(source.count_ruptures(), 32, msg)

    def test03(self):
        """ Simplest test - checking when standard floating is used """

        profiles = [Line([Point(0.0, 0.0, 0.0), Point(0.0, 0.001, 15.0)]),
                    Line([Point(0.1, 0.0, 0.0), Point(0.1, 0.010, 12.0)]),
                    Line([Point(0.2, 0.0, 0.0), Point(0.2, 0.020,  9.0)]),
                    Line([Point(0.3, 0.0, 0.0), Point(0.3, 0.030,  6.0)])]

        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.8, max_mag=6.2,
                             bin_width=0.1)

        source = self._make_source(mfd=mfd, aspect_ratio=1.5,
                                   profiles=profiles,
                                   floating_x_step=0, floating_y_step=0)

        msg = 'Wrong number of ruptures'
        self.assertEqual(source.count_ruptures(), 43, msg)

        if MAKE_MOVIES:
            ruptures = [r for r in source.iter_ruptures()]
            self._ruptures_animation('test03', source.surface, ruptures,
                                     source.profiles)

    def test04(self):
        """ As in test01, but reduces M to deal with ruptures and surfaces
        that have numbers of nodes that suitably scale with the floating
        factor """

        # Create the magnitude-frequency distribution
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.5, max_mag=5.6,
                             bin_width=0.1)
        source = self._make_source(mfd=mfd, aspect_ratio=1.5)

        # The fault surface created should contain 13 quadrilaterals along
        # the strike and 9 quadrilaterals along the dip. The distance between
        # the two profiles is 33 km. Given that we use a grid spacing of
        # 2.5 km, 2.5 * 13 gives 32.5 km. The grid spacing along dip is scaled
        # by the aspect ratio so that the sampling is proportional along
        # strike and dip. In this case the sampling along strike is 1.66km

        msg = 'Wrong surface mesh'
        self.assertEqual(source.surface.mesh.lons.shape[1], 14, msg)
        self.assertEqual(source.surface.mesh.lons.shape[0], 10, msg)

        # Regarding ruptures, the lowest magnitude admitted by the MFD is 6.25
        # hence - given that the corresponding area of the rupture is 178 km
        # and the aspect ratio is 1.5 the mesh covered by this rupture must
        # have the following dimensions:
        # - width = 10.68 km i.e. 6 quadrilaterals and 7 vertexes
        # - lenght = 16.02 km i.e. 7 quadrilaterals and 8 vertexes

        for idx, tmp in enumerate(source.iter_ruptures()):
            rup = tmp
            if idx == 0:
                break

        msg = 'Wrong dimension of the rupture'
        self.assertEqual(rup.surface.mesh.lons.shape[0], 4, msg)
        self.assertEqual(rup.surface.mesh.lons.shape[1], 4, msg)

        msg = 'Wrong number of ruptures'
        self.assertEqual(source.count_ruptures(), 24, msg)

        if MAKE_PICTURES:
            ppp(source.profiles, source.surface)

        if MAKE_MOVIES:
            ruptures = [r for r in source.iter_ruptures()]
            self._ruptures_animation('test04', source.surface, ruptures,
                                     source.profiles)

    def test05(self):
        """ Uses small rupture overlap fraction such that the mesh spacing
        is used instead """

        # Create the magnitude-frequency distribution
        mfd = TruncatedGRMFD(a_val=0.5, b_val=1.0, min_mag=5.5, max_mag=5.6,
                             bin_width=0.1)
        source = self._make_source(mfd=mfd, aspect_ratio=1.5,
                                   floating_x_step=0.1, floating_y_step=0.1)

        # The fault surface created should contain 13 quadrilaterals along
        # the strike and 9 quadrilaterals along the dip. The distance between
        # the two profiles is 33 km. Given that we use a grid spacing of
        # 2.5 km, 2.5 * 13 gives 32.5 km. The grid spacing along dip is scaled
        # by the aspect ratio so that the sampling is proportional along
        # strike and dip. In this case the sampling along strike is 1.66km

        msg = 'Wrong surface mesh'
        self.assertEqual(source.surface.mesh.lons.shape[1], 14, msg)
        self.assertEqual(source.surface.mesh.lons.shape[0], 10, msg)

        # Regarding ruptures, the lowest magnitude admitted by the MFD is 6.25
        # hence - given that the corresponding area of the rupture is 178 km
        # and the aspect ratio is 1.5 the mesh covered by this rupture must
        # have the following dimensions:
        # - width = 10.68 km i.e. 6 quadrilaterals and 7 vertexes
        # - lenght = 16.02 km i.e. 7 quadrilaterals and 8 vertexes

        for idx, tmp in enumerate(source.iter_ruptures()):
            rup = tmp
            if idx == 0:
                break

        msg = 'Wrong dimension of the rupture'
        self.assertEqual(rup.surface.mesh.lons.shape[0], 4, msg)
        self.assertEqual(rup.surface.mesh.lons.shape[1], 4, msg)

        msg = 'Wrong number of ruptures'
        self.assertEqual(source.count_ruptures(), 77, msg)

        if MAKE_PICTURES:
            ppp(source.profiles, source.surface)

        if MAKE_MOVIES:
            ruptures = [r for r in source.iter_ruptures()]
            self._ruptures_animation('test05', source.surface, ruptures,
                                     source.profiles)
