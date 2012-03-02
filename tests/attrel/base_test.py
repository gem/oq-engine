import unittest
import collections

import numpy

from nhe import const
from nhe.attrel.base import IPE, AttRelContext
from nhe.geo.point import Point
from nhe.imt import PGA, PGV
from nhe.site import Site
from nhe.source.rupture import Rupture


class _FakeAttRelTestCase(unittest.TestCase):
    DEFAULT_IMT = PGA
    DEFAULT_COMPONENT = const.IMC.GMRotI50

    def setUp(self):
        class FakeAttrel(IPE):
            DEFINED_FOR_TECTONIC_REGION_TYPES = set()
            DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
            DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS = set()
            DEFINED_FOR_STANDARD_DEVIATION_TYPES = set()
            REQUIRES_SITE_PARAMETERS = set()
            REQUIRES_RUPTURE_PARAMETERS = set()
            REQUIRES_DISTANCES = set()
            def get_mean_and_stddevs(self, context, imt, stddev_types,
                                     component_type):
                pass

        super(_FakeAttRelTestCase, self).setUp()
        self.attrel_class = FakeAttrel
        self.attrel = self.attrel_class()
        self.attrel.DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS.add(
            self.DEFAULT_COMPONENT
        )
        self.attrel.DEFINED_FOR_INTENSITY_MEASURE_TYPES.add(self.DEFAULT_IMT)

    def _get_poes(self, **kwargs):
        default_kwargs = dict(
            ctx=AttRelContext(),
            imts={self.DEFAULT_IMT(): [1.0, 2.0, 3.0]},
            component_type=self.DEFAULT_COMPONENT,
            truncation_level=1.0
        )
        default_kwargs.update(kwargs)
        kwargs = default_kwargs
        return self.attrel.get_poes(**kwargs)

    def _assert_value_error(self, func, error, **kwargs):
        with self.assertRaises(ValueError) as ar:
            func(**kwargs)
        self.assertEqual(str(ar.exception), error)


class GetPoEsWrongInputTestCase(_FakeAttRelTestCase):
    def test_wrong_imt(self):
        err = 'keys of imts dictionary must be instances of IMT classes'
        self._assert_value_error(self._get_poes, err, imts={'something': [3]})
        err = 'intensity measure type PGV is not supported by FakeAttrel'
        self._assert_value_error(self._get_poes, err,
                                 imts={PGA(): [1], PGV(): [5]})

    def test_wrong_components(self):
        err = "intensity measure component 'something' " \
              "is not supported by FakeAttrel"
        self._assert_value_error(self._get_poes, err,
                                 component_type='something')
        err = "intensity measure component 'Random horizontal' " \
              "is not supported by FakeAttrel"
        self._assert_value_error(self._get_poes, err,
                                 component_type=const.IMC.RANDOM_HORIZONTAL)

    def test_wrong_truncation_level(self):
        err = 'truncation level must be zero, positive number or None'
        self._assert_value_error(self._get_poes, err, truncation_level=-0.1)
        self._assert_value_error(self._get_poes, err, truncation_level=-1)

    def test_attrel_doesnt_support_total_stddev(self):
        with self.assertRaises(AssertionError) as ar:
            self._get_poes()
        self.assertEqual(
            ar.exception.message,
            'FakeAttrel does not support TOTAL standard deviation '
            'which is required for calculating probabilities of exceedance '
            'with non-zero truncation level'
        )

    def test_attrel_doesnt_support_rup_trt(self):
        ctx = AttRelContext()
        ctx.rup_trt = const.TRT.STABLE_CONTINENTAL
        err = "tectonic region type 'Stable Shallow Crust' " \
              "is not supported by FakeAttrel"
        self._assert_value_error(self._get_poes, err, ctx=ctx)


class GetPoEsTestCase(_FakeAttRelTestCase):
    def test_no_truncation(self):
        self.attrel_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )
        def get_mean_and_stddevs(ctx, imt, stddev_types, component_type):
            self.assertEqual(imt, self.DEFAULT_IMT())
            self.assertEqual(stddev_types, [const.StdDev.TOTAL])
            self.assertEqual(component_type, self.DEFAULT_COMPONENT)
            mean = -0.7872268528578843
            stddev = 0.5962393527251486
            get_mean_and_stddevs.call_count += 1
            return mean, [stddev]
        get_mean_and_stddevs.call_count = 0
        self.attrel.get_mean_and_stddevs = get_mean_and_stddevs
        iml = 0.6931471805599453
        iml_poes = self._get_poes(imts={self.DEFAULT_IMT(): [iml]},
                                  truncation_level=None)[self.DEFAULT_IMT()]
        self.assertIsInstance(iml_poes, numpy.ndarray)
        [poe] = iml_poes
        expected_poe = 0.006516701082128207
        self.assertAlmostEqual(poe, expected_poe, places=6)
        self.assertEqual(get_mean_and_stddevs.call_count, 1)

    def test_zero_truncation(self):
        def get_mean_and_stddevs(ctx, imt, stddev_types, component_type):
            return 1.1, [123.45]
        self.attrel.get_mean_and_stddevs = get_mean_and_stddevs
        imt = self.DEFAULT_IMT()
        imts = {imt: [0, 1, 2, 1.1, 1.05]}
        poes = self._get_poes(imts=imts, truncation_level=0)[imt]
        self.assertIsInstance(poes, numpy.ndarray)
        expected_poes = [0, 0, 1, 1, 0]
        self.assertEqual(list(poes), expected_poes)

        self.attrel_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )
        poes = self._get_poes(imts=imts, truncation_level=0)[imt]
        self.assertEqual(list(poes), expected_poes)

    def test_truncated(self):
        self.attrel_class.DEFINED_FOR_STANDARD_DEVIATION_TYPES.add(
            const.StdDev.TOTAL
        )
        def get_mean_and_stddevs(ctx, imt, stddev_types, component_type):
            return -0.7872268528578843, [0.5962393527251486]
        self.attrel.get_mean_and_stddevs = get_mean_and_stddevs
        imls = [-2.995732273553991, -0.6931471805599453, 0.6931471805599453]
        poes = self._get_poes(imts={self.DEFAULT_IMT(): imls},
                              truncation_level=2.0)[self.DEFAULT_IMT()]
        self.assertIsInstance(poes, numpy.ndarray)
        poe1, poe2, poe3 = poes
        self.assertEqual(poe1, 1)
        self.assertEqual(poe3, 0)
        self.assertAlmostEqual(poe2, 0.43432352175355504, places=6)


class MakeContextTestCase(_FakeAttRelTestCase):
    def setUp(self):
        super(MakeContextTestCase, self).setUp()
        self.site_location = Point(10, 20)
        self.site = Site(vs30=456, vs30measured=False,
                         z1pt0=12.1, z2pt5=15.1,
                         location=self.site_location)
        min_distance = 10
        rx_distance = 4
        jb_distance = 6
        top_edge_depth = 30
        self.distances = {'rrup': 123, 'rx': 456, 'ztor': 789, 'rjb': 779}
        class FakeSurface(object):
            call_counts = collections.Counter()
            def get_dip(self):
                self.call_counts['get_dip'] += 1
                return 45.4545
            def get_min_distance(fake_surface, point):
                self.assertEqual(point, self.site_location)
                fake_surface.call_counts['get_min_distance'] += 1
                return min_distance
            def get_rx_distance(fake_surface, point):
                self.assertEqual(point, self.site_location)
                fake_surface.call_counts['get_rx_distance'] += 1
                return rx_distance
            def get_joyner_boore_distance(fake_surface, point):
                self.assertEqual(point, self.site_location)
                fake_surface.call_counts['get_joyner_boore_distance'] += 1
                return jb_distance
            def get_top_edge_depth(fake_surface):
                fake_surface.call_counts['get_top_edge_depth'] += 1
                return top_edge_depth
        self.rupture_hypocenter = Point(20, 30, 40)
        self.rupture = Rupture(
            mag=123.45, rake=123.56,
            tectonic_region_type=const.TRT.VOLCANIC,
            hypocenter=self.rupture_hypocenter, surface=FakeSurface()
        )
        self.attrel_class.DEFINED_FOR_TECTONIC_REGION_TYPES.add(
            const.TRT.VOLCANIC
        )
        self.fake_surface = FakeSurface

    def test_unknown_site_param_error(self):
        self.attrel_class.REQUIRES_SITE_PARAMETERS.add('unknown!')
        err = "FakeAttrel requires unknown site parameter 'unknown!'"
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture)
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture,
                                 distances=self.distances)

    def test_unknown_rupture_param_error(self):
        self.attrel_class.REQUIRES_RUPTURE_PARAMETERS.add('stuff')
        err = "FakeAttrel requires unknown rupture parameter 'stuff'"
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture)
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture,
                                 distances=self.distances)

    def test_unknown_distance_error(self):
        self.attrel_class.REQUIRES_DISTANCES.add('jump height')
        err = "FakeAttrel requires unknown distance measure 'jump height'"
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture)
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture,
                                 distances=self.distances)

    def test_precalc_distance_is_missing_error(self):
        self.attrel_class.REQUIRES_DISTANCES |= set(('rjb', 'ztor'))
        distances = {'rjb': 444}
        err = "'distances' dict should include all the required distance " \
              "measures: rjb, ztor"
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture,
                                 distances=distances)

    def test_unsupported_trt_error(self):
        self.rupture.tectonic_region_type = const.TRT.SUBDUCTION_INTERFACE
        err = "tectonic region type 'Subduction Interface' " \
              "is not supported by FakeAttrel"
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture)
        self._assert_value_error(self.attrel.make_context, err,
                                 site=self.site, rupture=self.rupture,
                                 distances=self.distances)

    def test_all_values_no_precalc_distances(self):
        self.attrel_class.REQUIRES_DISTANCES = set('rjb ztor rx rrup'.split())
        self.attrel_class.REQUIRES_RUPTURE_PARAMETERS = set(
            'mag rake trt dip'.split()
        )
        self.attrel_class.REQUIRES_SITE_PARAMETERS = set(
            'vs30 vs30measured z1pt0 z2pt5'.split()
        )
        ctx = self.attrel.make_context(self.site, self.rupture)
        self.assertIsInstance(ctx, AttRelContext)
        self.assertEqual(ctx.rup_mag, 123.45)
        self.assertEqual(ctx.rup_rake, 123.56)
        self.assertEqual(ctx.rup_trt, const.TRT.VOLCANIC)
        self.assertEqual(ctx.rup_dip, 45.4545)
        self.assertEqual(ctx.site_vs30, 456)
        self.assertEqual(ctx.site_vs30measured, False)
        self.assertEqual(ctx.site_z1pt0, 12.1)
        self.assertEqual(ctx.site_z2pt5, 15.1)
        self.assertEqual(ctx.dist_rjb, 6)
        self.assertEqual(ctx.dist_rx, 4)
        self.assertEqual(ctx.dist_rrup, 10)
        self.assertEqual(ctx.dist_ztor, 30)
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_top_edge_depth': 1, 'get_rx_distance': 1,
                          'get_joyner_boore_distance': 1, 'get_dip': 1,
                          'get_min_distance': 1})

    def test_all_values_with_precalc_distances(self):
        self.attrel_class.REQUIRES_DISTANCES = set('rjb ztor rx rrup'.split())
        self.attrel_class.REQUIRES_RUPTURE_PARAMETERS = set(
            'mag rake trt dip'.split()
        )
        self.attrel_class.REQUIRES_SITE_PARAMETERS = set(
            'vs30 vs30measured z1pt0 z2pt5'.split()
        )
        ctx = self.attrel.make_context(self.site, self.rupture,
                                       distances=self.distances)
        self.assertEqual((ctx.rup_mag, ctx.rup_rake, ctx.rup_trt, ctx.rup_dip),
                         (123.45, 123.56, const.TRT.VOLCANIC, 45.4545))
        self.assertEqual((ctx.site_vs30, ctx.site_vs30measured,
                          ctx.site_z1pt0, ctx.site_z2pt5),
                         (456, False, 12.1, 15.1))
        self.assertEqual(ctx.dist_rrup, 123)
        self.assertEqual(ctx.dist_rx, 456)
        self.assertEqual(ctx.dist_ztor, 789)
        self.assertEqual(ctx.dist_rjb, 779)
        self.assertEqual(self.fake_surface.call_counts, {'get_dip': 1})

    def test_some_values_no_precalc_distances(self):
        self.attrel_class.REQUIRES_DISTANCES = set('rjb rx'.split())
        self.attrel_class.REQUIRES_RUPTURE_PARAMETERS = set('mag rake'.split())
        self.attrel_class.REQUIRES_SITE_PARAMETERS = set('vs30 z1pt0'.split())
        ctx = self.attrel.make_context(self.site, self.rupture)
        self.assertEqual((ctx.rup_mag, ctx.rup_rake), (123.45, 123.56))
        self.assertEqual((ctx.site_vs30, ctx.site_z1pt0), (456, 12.1))
        self.assertEqual((ctx.dist_rjb, ctx.dist_rx), (6, 4))
        self.assertFalse(hasattr(ctx, 'rup_trt'))
        self.assertFalse(hasattr(ctx, 'rup_dip'))
        self.assertFalse(hasattr(ctx, 'site_vs30measured'))
        self.assertFalse(hasattr(ctx, 'site_z2pt0'))
        self.assertFalse(hasattr(ctx, 'dist_rrup'))
        self.assertFalse(hasattr(ctx, 'dist_ztor'))
        self.assertEqual(self.fake_surface.call_counts,
                         {'get_rx_distance': 1,
                          'get_joyner_boore_distance': 1})

    def test_some_values_with_precalc_distances(self):
        self.attrel_class.REQUIRES_DISTANCES = set('ztor rrup'.split())
        self.attrel_class.REQUIRES_RUPTURE_PARAMETERS = set(('trt',))
        self.attrel_class.REQUIRES_SITE_PARAMETERS = set(('vs30measured',))
        distances = {'ztor': 17, 'rrup': 33}
        ctx = self.attrel.make_context(self.site, self.rupture,
                                       distances=distances)
        self.assertEqual(ctx.rup_trt, const.TRT.VOLCANIC)
        self.assertEqual(ctx.site_vs30measured, False)
        self.assertEqual(ctx.dist_ztor, 17)
        self.assertEqual(ctx.dist_rrup, 33)
        self.assertEqual(self.fake_surface.call_counts, {})
