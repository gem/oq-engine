import unittest
import csv
import os
import math

from nhe import const
from nhe.attrel.base import AttRelContext
from nhe.attrel.chiou_youngs_2008 import ChiouYoungs2008


class ChiouYoungs2008TestCase(unittest.TestCase):
    DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'CY08')

    def test_median_ms_hw_nm(self):
        datafile = os.path.join(self.DATA_PATH, 'CY08_MEDIAN_MS_HW_NM.csv')
        reader = csv.reader(open(datafile))
        params = reader.next()
        attrel = ChiouYoungs2008()

        for values in reader:
            values = dict(zip(params, map(float, values)))
            expected_results = {}
            context = AttRelContext()
            for param, value in values.items():
                if hasattr(context, param):
                    setattr(context, param, value)
                elif param == 'pga':
                    expected_results[const.IMT.PGA] = value
                elif param == 'pgv':
                    expected_results[const.IMT.PGV] = value
                else:
                    expected_results[(const.IMT.SA, float(param))] = value
            context.rup_rake = -70  # normal slip
            context.site_vs30type = const.VS30T.INFERRED

            for imt, expected_mean in expected_results.items():
                mean, stddev = attrel.get_mean_and_stddev(context, imt,
                                                          const.StdDev.NONE)
                mean = math.exp(mean)
                percentage = abs(mean / float(expected_mean) * 100 - 100)
                self.assertLess(percentage, 0.5)

    def test_sigmeas_ms_hw_ss(self):
        datafile = os.path.join(self.DATA_PATH, 'CY08_SIGMEAS_MS_HW_SS.csv')
        reader = csv.reader(open(datafile))
        params = reader.next()
        attrel = ChiouYoungs2008()

        for values in reader:
            values = dict(zip(params, map(float, values)))
            expected_results = {}
            context = AttRelContext()
            for param, value in values.items():
                if hasattr(context, param):
                    setattr(context, param, value)
                elif param == 'pga':
                    expected_results[const.IMT.PGA] = value
                elif param == 'pgv':
                    expected_results[const.IMT.PGV] = value
                else:
                    expected_results[(const.IMT.SA, float(param))] = value
            context.rup_rake = 0  # strike slip
            context.site_vs30type = const.VS30T.MEASURED

            for imt, expected_stddev in expected_results.items():
                mean, stddev = attrel.get_mean_and_stddev(context, imt,
                                                          const.StdDev.TOTAL)
                percentage = abs(stddev / float(expected_stddev) * 100 - 100)
                self.assertLess(percentage, 0.5)
