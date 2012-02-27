import unittest

import numpy

from nhe import const
from nhe.attrel.base import AttenuationRelationship, AttRelContext
from nhe.imt import PGA, PGV


class _FakeAttRelTestCase(unittest.TestCase):
    DEFAULT_IMT = PGA
    DEFAULT_COMPONENT = const.IMC.GMRotI50

    class FakeAttrel(AttenuationRelationship):
        DEFINED_FOR_TECTONIC_REGION_TYPES = None
        DEFINED_FOR_INTENSITY_MEASURE_TYPES = None
        DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS = None
        DEFINED_FOR_STANDARD_DEVIATION_TYPES = None
        REQUIRES_SITE_PARAMETERS = None
        REQUIRES_RUPTURE_PARAMETERS = None
        REQUIRES_DISTANCES = None

        def __init__(self):
            self.DEFINED_FOR_TECTONIC_REGION_TYPES = set()
            self.DEFINED_FOR_INTENSITY_MEASURE_TYPES = set()
            self.DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS = set()
            self.DEFINED_FOR_STANDARD_DEVIATION_TYPES = set()
            self.REQUIRES_SITE_PARAMETERS = set()
            self.REQUIRES_RUPTURE_PARAMETERS = set()
            self.REQUIRES_DISTANCES = set()

        def get_mean_and_stddevs(self, context, imt, stddev_types,
                                 component_type):
            pass

    def setUp(self):
        super(_FakeAttRelTestCase, self).setUp()
        self.attrel = self.FakeAttrel()
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
        return self.attrel.get_probabilities_of_exceedance(**kwargs)

    def _assert_error(self, error, **kwargs):
        with self.assertRaises(ValueError) as ar:
            self._get_poes(**kwargs)
        self.assertEqual(str(ar.exception), error)


class GetProbabilitiesOfExceedanceWrongInputTestCase(_FakeAttRelTestCase):
    def test_wrong_imt(self):
        err = 'keys of imts dictionary must be instances of IMT classes'
        self._assert_error(err, imts={'something': [3]})
        err = 'intensity measure type PGV is not supported by FakeAttrel'
        self._assert_error(err, imts={PGA(): [1], PGV(): [5]})

    def test_wrong_components(self):
        err = "intensity measure component 'something' " \
              "is not supported by FakeAttrel"
        self._assert_error(err, component_type='something')
        err = "intensity measure component 'Random horizontal' " \
              "is not supported by FakeAttrel"
        self._assert_error(err, component_type=const.IMC.RANDOM_HORIZONTAL)

    def test_wrong_truncation_level(self):
        err = 'truncation level must be positive'
        self._assert_error(err, truncation_level=-0.1)
        self._assert_error(err, truncation_level=-1)


class GetProbabilitiesOfExceedanceTestCase(_FakeAttRelTestCase):
    def test_no_truncation(self):
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
        poes = self._get_poes(imts={self.DEFAULT_IMT(): [0, 1, 2, 1.1, 1.05]},
                              truncation_level=0)[self.DEFAULT_IMT()]
        self.assertIsInstance(poes, numpy.ndarray)
        expected_poes = [0, 0, 1, 1, 0]
        self.assertEqual(list(poes), expected_poes)

    def test_truncated(self):
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
