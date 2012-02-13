import unittest

from nhe import const
from nhe.geo import Point
from nhe.geo.surface.planar import PlanarSurface
from nhe.geo.nodalplane import NodalPlane
from nhe.tom import PoissonTOM
from nhe.source.rupture import Rupture, ProbabilisticRupture


class RuptureCreationTestCase(unittest.TestCase):
    def make_rupture(self, rupture_class, **kwargs):
        default_arguments = {
            'mag': 5.5,
            'nodal_plane': NodalPlane(1, 2, 3),
            'tectonic_region_type': const.TRT.STABLE_CONTINENTAL,
            'hypocenter': Point(5, 6, 7),
            'surface': PlanarSurface(10,
                Point(0, 0, 1), Point(1, 0, 1),
                Point(1, 0, 2), Point(0, 0, 2)
            )
        }
        default_arguments.update(kwargs)
        kwargs = default_arguments
        rupture = rupture_class(**kwargs)
        for key in kwargs:
            self.assertIs(getattr(rupture, key), kwargs[key])

    def assert_failed_creation(self, rupture_class, exc, msg, **kwargs):
        with self.assertRaises(exc) as ae:
            self.make_rupture(rupture_class, **kwargs)
        self.assertEqual(ae.exception.message, msg)

    def test_wrong_trt(self):
        self.assert_failed_creation(Rupture, ValueError,
            "unknown tectonic region type 'Swamp'",
            tectonic_region_type='Swamp'
        )

    def test_negative_magnitude(self):
        self.assert_failed_creation(Rupture, ValueError,
            'magnitude must be positive',
            mag=-1
        )

    def test_zero_magnitude(self):
        self.assert_failed_creation(Rupture, ValueError,
            'magnitude must be positive',
            mag=0
        )

    def test_hypocenter_in_the_air(self):
        self.assert_failed_creation(Rupture, ValueError,
            'rupture hypocenter must have positive depth',
            hypocenter=Point(0, 1, -0.1)
        )

    def test_probabilistic_rupture_negative_occurrence_rate(self):
        self.assert_failed_creation(ProbabilisticRupture, ValueError,
            'occurrence rate must be positive',
            occurrence_rate=-1, temporal_occurrence_model=PoissonTOM(10)
        )

    def test_probabilistic_rupture_zero_occurrence_rate(self):
        self.assert_failed_creation(ProbabilisticRupture, ValueError,
            'occurrence rate must be positive',
            occurrence_rate=0, temporal_occurrence_model=PoissonTOM(10)
        )
