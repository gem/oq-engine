# vim: tabstop=4 shiftwidth=4 softtabstop=4

import unittest

class ExampleTestCase(unittest.TestCase):
    def setUp(self):
        self.tested = False

    def tearDown(self):
        pass

    def testBasic(self):
        self.assert_(not self.tested)
        self.tested = True 
        self.assert_(self.tested)
