import unittest

from nhe.const import TRT
from nhe.msr import Peer
from nhe.mfd import TruncatedGR
from nhe.common.geo import Point, Polygon
from nhe.common.pmf import PMF
from nhe.common.nodalplane import NodalPlane
from nhe.common.tom import PoissonTOM
from nhe.source.area import AreaSource


class AreaSourceIterRupturesTestCase(unittest.TestCase):
    def make_point_source(self, polygon, discretization, **kwargs):
        default_arguments = {
            'source_id': 'source_id', 'name': 'area source name',
            'tectonic_region_type': TRT.VOLCANIC,
            'mfd': TruncatedGR(a_val=3, b_val=1, min_mag=5,
                               max_mag=7, bin_width=1),
            'nodal_plane_distribution': PMF([(1, NodalPlane(1, 2, 3))]),
            'hypocenter_distribution': PMF([(1, 4)]),
            'upper_seismogenic_depth': 1.3,
            'lower_seismogenic_depth': 4.9,
            'magnitude_scaling_relationship': Peer(),
            'rupture_aspect_ratio': 1.333,
            'polygon': polygon,
            'area_discretization': discretization
        }
        default_arguments.update(kwargs)
        kwargs = default_arguments
        source = AreaSource(**kwargs)
        for key in kwargs:
            self.assertIs(getattr(source, key), kwargs[key])
        return source

    def test_1(self):
        source = self.make_point_source(
            Polygon([Point(-2, -2), Point(0, -2), Point(0, 0), Point(-2, 0)]),
            discretization=70
        )
        ruptures = list(source.iter_ruptures(PoissonTOM(50)))
        self.assertEqual(len(ruptures), 8 * 2)
