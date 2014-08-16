import unittest
from openquake.commonlib import sap


def f(a, b, c, d=1):
    return [a, b, c, d]


class SapTestCase(unittest.TestCase):
    def test_ok(self):
        p = sap.Parser(f)
        p.arg('a', 'first argument')
        p.opt('b', 'second argument')
        p.flg('c', 'third argument')
        p.opt('d', 'fourth argument')
        self.assertEqual(
            ['1', '2', False, '3'], p.callfunc('1 -b=2 -d=3'.split()))

    def test_NameError(self):
        p = sap.Parser(f)
        p.arg('a', 'first argument')
        with self.assertRaises(NameError):
            p.flg('c', 'third argument')
