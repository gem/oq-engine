# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
Implements the tests for the set of GMPE classes included within the
GMPE of Ameri et al (2017)
"""
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
import pathlib
from openquake.hazardlib import gsim, imt, const
import numpy as np
import unittest


data = pathlib.Path(__file__).parent / 'data'

# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.1
STDDEV_DISCREP = 0.1
# Translated precision, in number of decimals:
MEAN_DECIMAL = np.abs(np.round(np.log10(MEAN_DISCREP*0.01)))
STDDEV_DECIMAL = np.abs(np.round(np.log10(STDDEV_DISCREP*0.01)))


class AmeriEtAl2017RjbTestCase(BaseGSIMTestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the heteroscedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.AmeriEtAl2017Rjb
    # File containing the results for the Mean
    MEAN_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_MEAN.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_TOTAL_STDDEV.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_INTER_EVENT_STDDEV.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "AMERI2017/A17_Rjb_Heteroscedastic_INTRA_EVENT_STDDEV.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)

    def test_std_total(self):
        self.check(self.STD_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)

    def test_std_inter(self):
        self.check(self.INTER_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)


class AmeriEtAl2017RepiTestCase(AmeriEtAl2017RjbTestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which epicentral
    distance is the preferred distance metric, and standard deviation
    is provided using the heteroscedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.AmeriEtAl2017Repi
    MEAN_FILE = "AMERI2017/A17_Repi_Heteroscedastic_MEAN.csv"
    STD_FILE = "AMERI2017/A17_Repi_Heteroscedastic_TOTAL_STDDEV.csv"
    INTER_FILE = "AMERI2017/A17_Repi_Heteroscedastic_INTER_EVENT_STDDEV.csv"
    INTRA_FILE = "AMERI2017/A17_Repi_Heteroscedastic_INTRA_EVENT_STDDEV.csv"


class AmeriEtAl2017RjbStressDropTestCase(unittest.TestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the homoscedastic formulation
    """

    def test_calculation_mean(self):

        DATA_FILE = data / "AMERI2017/A17_Rjb_Homoscedastic_MEAN.csv"
        stddev_types = [const.StdDev.TOTAL]  # Unused here
        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'rjb', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                ctx.sids = [0]
                damp = arr[6]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RjbStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = np.log(arr[7+k])
                    # convert value to ln(SA) with SA in units of g
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    mean = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                     stddev_types)[0]
                    np.testing.assert_almost_equal(
                        mean, value, decimal=MEAN_DECIMAL)

    def test_calculation_std_total(self):

        DATA_FILE = data/"AMERI2017/A17_Rjb_Homoscedastic_TOTAL_STDDEV.csv"
        stddev_types = [const.StdDev.TOTAL]
        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:] # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'rjb', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                ctx.sids = [0]
                damp = arr[6]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RjbStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = arr[7+k]
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    std = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                    stddev_types)[1][0]
                    np.testing.assert_almost_equal(
                        std, value, decimal=STDDEV_DECIMAL)

    def test_calculation_std_intra(self):

        DATA_FILE = data/"AMERI2017/A17_Rjb_Homoscedastic_INTRA_EVENT_STDDEV.csv"
        stddev_types = [const.StdDev.INTRA_EVENT]

        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'rjb', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                damp = arr[6]
                ctx.sids = [0]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RjbStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = arr[7+k]
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    std = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                    stddev_types)[1][0]
                    np.testing.assert_almost_equal(
                        std, value, decimal=STDDEV_DECIMAL)

    def test_calculation_std_inter(self):

        DATA_FILE = data/"AMERI2017/A17_Rjb_Homoscedastic_INTER_EVENT_STDDEV.csv"
        stddev_types = [const.StdDev.INTER_EVENT]

        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'rjb', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                damp = arr[6]
                ctx.sids = [0]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RjbStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = arr[7+k]
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    std = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                    stddev_types)[1][0]
                    np.testing.assert_almost_equal(
                        std, value, decimal=STDDEV_DECIMAL)


class AmeriEtAl2017RepiStressDropTestCase(unittest.TestCase):
    """
    Tests the Ameri et al (2017) GMPE for the case in which epicentral
    distance is the preferred distance metric, and standard deviation
    is provided using the homoscedastic formulation
    """

    def test_calculation_mean(self):

        DATA_FILE = data / "AMERI2017/A17_Repi_Homoscedastic_MEAN.csv"
        stddev_types = [const.StdDev.TOTAL]  # Unused here

        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'repi', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                damp = arr[6]
                ctx.sids = [0]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RepiStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = np.log(arr[7+k])
                    # convert value to ln(SA) with SA in units of g
                    if per=='pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    mean = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                     stddev_types)[0]
                    np.testing.assert_almost_equal(
                        mean, value, decimal=MEAN_DECIMAL)

    def test_calculation_std_total(self):

        DATA_FILE = data/"AMERI2017/A17_Repi_Homoscedastic_TOTAL_STDDEV.csv"
        stddev_types = [const.StdDev.TOTAL]

        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'repi', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                damp = arr[6]
                ctx.sids = [0]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RepiStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = arr[7+k]
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    std = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                    stddev_types)[1][0]
                    np.testing.assert_almost_equal(
                        std, value, decimal=STDDEV_DECIMAL)

    def test_calculation_std_intra(self):

        DATA_FILE = data/"AMERI2017/A17_Repi_Homoscedastic_INTRA_EVENT_STDDEV.csv"
        stddev_types = [const.StdDev.INTRA_EVENT]

        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'repi', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                damp = arr[6]
                ctx.sids = [0]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RepiStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = arr[7+k]
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    std = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                    stddev_types)[1][0]
                    np.testing.assert_almost_equal(
                        std, value, decimal=STDDEV_DECIMAL)

    def test_calculation_std_inter(self):

        DATA_FILE = data/"AMERI2017/A17_Repi_Homoscedastic_INTER_EVENT_STDDEV.csv"
        stddev_types = [const.StdDev.INTER_EVENT]

        ctx = gsim.base.RuptureContext()

        with open(DATA_FILE, 'r') as f:

            # Read periods from header:
            header = f.readline()
            periods = header.strip().split(',')[7:]  # Periods in s.

            for line in f:
                arr_str = line.strip().split(',')
                arr_str[5] = "9999"
                # Replace result_type string by any float-convertible value
                arr = np.float_(arr_str)

                # Setting ground-motion attributes:
                setattr(ctx, 'mag', arr[0])
                setattr(ctx, 'rake', arr[1])
                stress_drop = arr[2]
                setattr(ctx, 'repi', arr[3])
                setattr(ctx, 'vs30', np.array([arr[4]]))
                damp = arr[6]
                ctx.sids = [0]

                # Compute ground-motion:
                gmpe = gsim.ameri_2017.AmeriEtAl2017RepiStressDrop(
                    norm_stress_drop=stress_drop)
                for k in range(len(periods)):
                    per = periods[k]
                    value = arr[7+k]
                    if per == 'pga':
                        P = imt.PGA()
                    else:
                        P = imt.SA(period=np.float_(per), damping=damp)
                    std = gmpe.get_mean_and_stddevs(ctx, ctx, ctx, P,
                                                    stddev_types)[1][0]
                    np.testing.assert_almost_equal(std, value,
                                                   decimal=STDDEV_DECIMAL)


# Discrepancy percentages to be applied to all tests
MEAN_DISCREP = 0.01
STDDEV_DISCREP = 0.01


class Ameri2014TestCase(BaseGSIMTestCase):
    """
    Tests the Ameri (2014) GMPE for the case in which Joyner-Boore
    distance is the preferred distance metric, and standard deviation
    is provided using the homoskedastic formulation
    """
    GSIM_CLASS = gsim.ameri_2017.Ameri2014Rjb
    # File containing the results for the Mean
    MEAN_FILE = "ameri14/Ameri_2014_mean.csv"
    # File contaning the results for the Total Standard Deviation
    STD_FILE = "ameri14/Ameri_2014_total_stddev.csv"
    # File contaning the results for the Inter-Event Standard Deviation
    INTER_FILE = "ameri14/Ameri_2014_inter_event_stddev.csv"
    # File contaning the results for the Intra-Event Standard Deviation
    INTRA_FILE = "ameri14/Ameri_2014_intra_event_stddev.csv"

    def test_mean(self):
        self.check(self.MEAN_FILE,
                   max_discrep_percentage=MEAN_DISCREP)

    def test_std_total(self):
        self.check(self.STD_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)

    def test_std_inter(self):
        self.check(self.INTER_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)

    def test_std_intra(self):
        self.check(self.INTRA_FILE,
                   max_discrep_percentage=STDDEV_DISCREP)
