# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Comprehensive test suite for the Al Atik (2015) aleatory uncertainty model
for the NGA East model set

Data compared against tables taken from the Al Atik (2015) report:

For inter-event standard deviation (tau): Tables 5.4, 5.5 and 5.6

For single-station intra-event standard deviation (phi_ss): Tables 5.11, 5.12
and 5.13

For delta_s2s: Table 5.15
"""
import os
import inspect
import unittest
import numpy as np
from nose.plugins.attrib import attr
from openquake.hazardlib.tests.gsim.check_gsim import check_gsim
from openquake.hazardlib.gsim.nga_east import DarraghEtAl2015NGAEast1CCSP

# Use a reference GMPE, it doesn't matter which as the mean is not being tested
DUMMY_GSIM = DarraghEtAl2015NGAEast1CCSP


# From Al Atik (2015) three branches are defined that correspond to epistemic
# quantile: low (0.05), central (0.5) and high (0.95)
QUANTILE = {"low": 0.05, "central": 0.5, "high": 0.95}

# In this case discrepancy of 0.1 % is tolerated
MAX_DISC = 0.1


# Comprehensive suite of test files
NGA_EAST_SIGMA_FILES = [
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_LOW_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_CENTRAL_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_GLOBAL_HIGH_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_LOW_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_CENTRAL_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA-CONSTANT_HIGH_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_LOW_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_CENTRAL_PHI_CENA_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_GLOBAL_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA-CONSTANT_HIGH_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_LOW_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_LOW_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_LOW_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_LOW_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_LOW_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_LOW_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_CENTRAL_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_CENTRAL_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_CENTRAL_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_CENTRAL_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_CENTRAL_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_CENTRAL_ERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_HIGH_NONERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_HIGH_NONERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_HIGH_NONERGODIC_HIGH",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_HIGH_ERGODIC_LOW",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_HIGH_ERGODIC_CENTRAL",
    "nga_east_all_stddev_tables/TAU_CENA_HIGH_PHI_CENA_HIGH_ERGODIC_HIGH"
    ]


@attr('slow')
class NGAEastUncertaintyTestCase(unittest.TestCase):
    """
    Variant of the :class:
    `openquake.hazardlib.tests.gsim.utils.BaseGSIMTestCase` object in which
    the GSIM is passed to the check function

    This object checks all of the various aleatory uncertainty models to
    in which the choice of model and quantile are input numerically, but then
    compared against the "epistemic" tables in Chapter 5 of Al Atik (2015)
    in which, tau, phi and phi_s2ss are described in terms of a "low",
    "central" and "high" branch
    """
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

    def get_context_attributes(self, ctx):
        att = inspect.getmembers(ctx, lambda a: not inspect.isroutine(a))
        att = [k for k, v in att if '_abc' not in k
               and not (k.startswith('_') and k.endswith('_'))]
        return set(att)

    def check(self, gsim, filename, max_discrep_percentage):
        filename = os.path.join(self.BASE_DATA_PATH, filename)
        errors, stats, sctx, rctx, dctx, ctxs = check_gsim(
            gsim, open(filename), max_discrep_percentage)
        s_att = self.get_context_attributes(sctx)
        r_att = self.get_context_attributes(rctx)
        d_att = self.get_context_attributes(dctx)
        self.assertEqual(gsim.REQUIRES_SITES_PARAMETERS, s_att)
        self.assertEqual(gsim.REQUIRES_RUPTURE_PARAMETERS, r_att)
        self.assertEqual(gsim.REQUIRES_DISTANCES, d_att)
        self.assertTrue(
            np.all(ctxs),
            msg='Contexts objects have been changed by method '
                'get_mean_and_stddevs')
        if errors:
            raise AssertionError(stats)
        print()
        print(stats)

    def _test_uncertainty_model(self, gsim, filestem, max_disc=MAX_DISC):
        """
        Each uncertainty model describes an inter-event, intra-event and total
        standard deviation, so three checks are executed.
        """
        # INTER-EVENT
        self.check(gsim, filestem + "_INTER_STDDEV.csv", max_disc)
        # INTRA-EVENT
        self.check(gsim, filestem + "_INTRA_STDDEV.csv", max_disc)
        # TOTAL
        self.check(gsim, filestem + "_TOTAL_STDDEV.csv", max_disc)

    def test_all_nga_east_uncertainty(self):
        """
        Tests every permuration of NGA East aleatory uncertainty model.
        NGA_EAST_SIGMA_FILES describes each uncertainty model, with each
        permutation defining separate tests of inter-event, intra-event and
        total standard deviation
        """
        for filestem in NGA_EAST_SIGMA_FILES:
            filestring = os.path.split(filestem)[1]
            # Break filestem into model configuration
            config_params = [key.lower() for key in filestring.split("_")]
            # Retrieve model configuation parameters
            _, tau_model, tau_branch, _, phi_model, phi_branch,\
                phi_s2ss_model, phi_s2ss_branch = config_params
            tau_quantile = QUANTILE[tau_branch]
            phi_quantile = QUANTILE[phi_branch]
            # If the cena constant branch is being considered then need to
            # replace the "-" with a "_"
            tau_model = tau_model.replace("cena-constant", "cena_constant")
            phi_model = phi_model.replace("cena-constant", "cena_constant")
            if phi_s2ss_model.upper() == "ERGODIC":
                phi_s2ss_model = "cena"
            else:
                phi_s2ss_model = None
            phi_s2ss_quantile = QUANTILE[phi_s2ss_branch]
            # Instantiate GSIM
            gsim = DUMMY_GSIM(tau_model=tau_model, phi_model=phi_model,
                              phi_s2ss_model=phi_s2ss_model,
                              tau_quantile=tau_quantile,
                              phi_ss_quantile=phi_quantile,
                              phi_s2ss_quantile=phi_s2ss_quantile)
            # Run Checks
            self._test_uncertainty_model(gsim, filestem, MAX_DISC)
