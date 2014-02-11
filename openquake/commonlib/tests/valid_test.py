import unittest
from openquake.commonlib import valid


class ValidationTestCase(unittest.TestCase):

    def test_name(self):
        self.assertEqual(valid.name('x'), 'x')
        with self.assertRaises(ValueError):
            valid.name('1')
        with self.assertRaises(ValueError):
            valid.name('x y')

    def test_namelist(self):
        self.assertEqual(valid.namelist('x y'), ['x', 'y'])
        with self.assertRaises(ValueError):
            valid.namelist('')
        with self.assertRaises(ValueError):
            valid.namelist('x 1')

    def test_longitude(self):
        self.assertEqual(valid.longitude('1'), 1.0)
        self.assertEqual(valid.longitude('180'), 180.0)
        with self.assertRaises(ValueError):
            valid.longitude('181')
        with self.assertRaises(ValueError):
            valid.longitude('-181')

    def test_latitude(self):
        self.assertEqual(valid.latitude('1'), 1.0)
        self.assertEqual(valid.latitude('90'), 90.0)
        with self.assertRaises(ValueError):
            valid.latitude('91')
        with self.assertRaises(ValueError):
            valid.latitude('-91')

    def test_positiveint(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positiveint('-1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.1')
        with self.assertRaises(ValueError):
            valid.positiveint('1.0')

    def test_positivefloat(self):
        self.assertEqual(valid.positiveint('1'), 1)
        with self.assertRaises(ValueError):
            valid.positivefloat('-1')
        self.assertEqual(valid.positivefloat('1.1'), 1.1)

    def test_probability(self):
        self.assertEqual(valid.probability('1'), 1.0)
        self.assertEqual(valid.probability('.5'), 0.5)
        self.assertEqual(valid.probability('0'), 0.0)
        with self.assertRaises(ValueError):
            valid.probability('1.1')
        with self.assertRaises(ValueError):
            valid.probability('-0.1')

    def test_IMTstr(self):
        self.assertEqual(valid.IMTstr('SA(1)'), ('SA', 1, 5))
        self.assertEqual(valid.IMTstr('SA(1.)'), ('SA', 1, 5))
        self.assertEqual(valid.IMTstr('SA(0.5)'), ('SA', 0.5, 5))
        self.assertEqual(valid.IMTstr('PGV'), ('PGV', None, None))
        with self.assertRaises(ValueError):
            valid.IMTstr('S(1)')

    def test_choice(self):
        validator = valid.Choice('aggregated', 'per_asset')
        self.assertEqual(validator('aggregated'), 'aggregated')
        self.assertEqual(validator('per_asset'), 'per_asset')
        with self.assertRaises(ValueError):
            validator('xxx')

    def test_empty(self):
        self.assertEqual(valid.not_empty("text"), "text")
        with self.assertRaises(ValueError):
            valid.not_empty("")

    def test_boolean(self):
        self.assertEqual(valid.boolean('0'), False)
        self.assertEqual(valid.boolean('1'), True)
        self.assertEqual(valid.boolean('false'), False)
        self.assertEqual(valid.boolean('true'), True)
        with self.assertRaises(ValueError):
            valid.boolean('')
        with self.assertRaises(ValueError):
            valid.boolean('xxx')
        with self.assertRaises(ValueError):
            valid.boolean('True')
        with self.assertRaises(ValueError):
            valid.boolean('False')

    def test_none_or(self):
        validator = valid.NoneOr(valid.boolean)
        self.assertEqual(validator(''), None)
        with self.assertRaises(ValueError):
            validator('xxx')
