import unittest

from nhe.mfd.base import BaseMFD


class BaseMFDTestCase(unittest.TestCase):
    class BaseTestMFD(BaseMFD):
        PARAMETERS = ()
        MODIFICATIONS = set()
        check_constraints_call_count = 0
        def check_constraints(self):
            self.check_constraints_call_count += 1
        def get_annual_occurrence_rates(self):
            pass

    def assert_mfd_error(self, func, *args, **kwargs):
        with self.assertRaises(ValueError) as exc_catcher:
            func(*args, **kwargs)
        return exc_catcher.exception


class BaseMFDSetParametersTestCase(BaseMFDTestCase):
    def test_missing(self):
        class TestMFD(self.BaseTestMFD):
            PARAMETERS = ('foo', 'bar', 'baz')
        exc = self.assert_mfd_error(TestMFD, foo=1)
        self.assertEqual(exc.message,
                         'These parameters are required but missing: bar, baz')

    def test_unexpected(self):
        class TestMFD(self.BaseTestMFD):
            PARAMETERS = ('foo', 'bar')
        exc = self.assert_mfd_error(TestMFD, foo=1, bar=2, baz=3)
        self.assertEqual(exc.message, 'These parameters are unexpected: baz')

    def test_check_constraints_is_called(self):
        class TestMFD(self.BaseTestMFD):
            PARAMETERS = ('foo', 'bar')
        mfd = TestMFD(foo=1, bar=2)
        self.assertEqual(mfd.check_constraints_call_count, 1)

    def test_parameters_are_assigned(self):
        class TestMFD(self.BaseTestMFD):
            PARAMETERS = ('baz', 'quux')
        mfd = TestMFD(baz=1, quux=True)
        self.assertEqual(mfd.baz, 1)
        self.assertEqual(mfd.quux, True)


class BaseMFDModificationsTestCase(BaseMFDTestCase):
    def test_modify_missing_method(self):
        class TestMFD(self.BaseTestMFD):
            MODIFICATIONS = ('foo', 'bar')
        mfd = TestMFD()
        exc = self.assert_mfd_error(mfd.modify, 'baz', {})
        self.assertEqual(exc.message,
                         'Modification baz is not supported by TestMFD')

    def test_modify(self):
        class TestMFD(self.BaseTestMFD):
            MODIFICATIONS = ('foo', )
            foo_calls = []
            def modify_foo(self, **kwargs):
                self.foo_calls.append(kwargs)
        mfd = TestMFD()
        self.assertEqual(mfd.check_constraints_call_count, 1)
        mfd.modify('foo', dict(a=1, b='2', c=True))
        self.assertEqual(mfd.foo_calls, [{'a': 1, 'b': '2', 'c': True}])
        self.assertEqual(mfd.check_constraints_call_count, 2)

    def test_reset(self):
        class TestMFD(self.BaseTestMFD):
            PARAMETERS = ('abc', 'defg')
        mfd = TestMFD(abc=1, defg=None)
        mfd.abc = 3
        mfd.defg = []
        mfd.reset()
        self.assertEqual(mfd.abc, 1)
        self.assertEqual(mfd.defg, None)
        self.assertEqual(mfd.check_constraints_call_count, 2)
