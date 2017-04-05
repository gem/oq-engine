#!/usr/bin/env python

'''
Module to test :class: openquake.hmtk.faults.mfd.base.BaseMFDfromSlip  and the additional
function openquake.hmtk.faults.mfd.base._scale_moment
'''

import unittest
from math import log10
from openquake.hmtk.faults.mfd.base import BaseMFDfromSlip, _scale_moment

class TestScaleMoment(unittest.TestCase):
    '''
    Tests the small ancillary function openquake.hmtk.fault.mfd.base._scale_moment, which
    converts a moment magnitude into a scalar moment
    '''
    def setUp(self):
        '''
        '''
        self.func = _scale_moment
        self.magnitude = 7.0

    def test_scale_moment_function(self):
        '''
        Tests the scale moment function
        '''

        # Case 1 - Moment in dyne-cm
        self.assertAlmostEqual(26.55,
                               log10(self.func(self.magnitude, in_nm=False)))
        # Case 2 - Moment in N-m
        self.assertAlmostEqual(19.55,
                               log10(self.func(self.magnitude, in_nm=True)))
