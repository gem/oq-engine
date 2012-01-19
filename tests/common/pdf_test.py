import unittest

from nhe.common.pdf import Poisson


class PoissonPDFTestCase(unittest.TestCase):
    def test_get_probability(self):
        pdf = Poisson(time_span=50)
        self.assertEqual(pdf.get_probability(occurrence_rate=10), 1)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability(occurrence_rate=0.1), 0.9932621)
        aae(pdf.get_probability(occurrence_rate=0.01), 0.39346934)

        pdf = Poisson(time_span=5)
        self.assertEqual(pdf.get_probability(occurrence_rate=8), 1)
        aae = self.assertAlmostEqual
        aae(pdf.get_probability(occurrence_rate=0.1), 0.3934693)
        aae(pdf.get_probability(occurrence_rate=0.01), 0.0487706)
