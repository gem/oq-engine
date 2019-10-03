import os
import numpy
import unittest

import openquake.hazardlib.calc.hazard_curve_ne as hcne
import openquake.hazardlib.calc.hazard_curve as hc

from openquake.hazardlib.const import TRT
from openquake.baselib.general import DictArray
from openquake.hazardlib.calc.filters import SourceFilter

from openquake.hazardlib.polynomial_chaos import get_hermite
from openquake.hazardlib.tests.gsim.mgmpe.dummy import Dummy
from openquake.hazardlib.mfd import EvenlyDiscretizedMFD
from openquake.hazardlib.source import CharacteristicFaultSource
from openquake.hazardlib.tom import PoissonTOM

from openquake.hazardlib.gsim.abrahamson_2014 import \
    AbrahamsonEtAl2014NonErgodic

BASE_PATH = os.path.dirname(__file__)


class CalcHazardTest(unittest.TestCase):

    def setUp(self):
        self.trt = TRT.ACTIVE_SHALLOW_CRUST
        # Parameters
        self.param = {}
        imtls = DictArray({'PGA': [0.1, 0.2, 0.3, 0.4],
                           'SA(0.5)': [0.1, 0.2, 0.3, 0.4, 0.5]})
        self.param['imtls'] = imtls
        # Setting information about the source
        id = '1'
        nme = 'test'
        trt = TRT.ACTIVE_SHALLOW_CRUST
        mfd = EvenlyDiscretizedMFD(6.0, 0.1, [0.1])
        tom = PoissonTOM(1.0)
        rup = Dummy.get_rupture(mag=6.0, hyp_lon=-121.0, hyp_lat=38.5)
        sfc = rup.surface
        rake = 90.
        self.src = CharacteristicFaultSource(id, nme, trt, mfd, tom, sfc, rake)
        # Creating the sites
        self.sitesc = Dummy.get_site_collection(2,
                                                hyp_lon=-120.9,
                                                hyp_lat=38.5,
                                                vs30=500.,
                                                vs30measured=True,
                                                z1pt0=50.)

    def test_kuehn2019ne(self):

        PLOTTING = True
        S = 0
        key = 'SA(0.01)'
        num_samples = 500
        num_samples_mc = 50

        gsim = AbrahamsonEtAl2014NonErgodic()
        gsims = {TRT.ACTIVE_SHALLOW_CRUST: gsim}
        s_filter = SourceFilter(self.sitesc, {TRT.ACTIVE_SHALLOW_CRUST: 200.})
        groups = [self.src, self.src]
        imtls = {'SA(0.01)': [0.01, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4]}

        pce_list = []
        for i, pcec in enumerate(hcne.calc_hazard_curves(groups, s_filter,
                                                         imtls, gsims)):
            if i == 0:
                pcea = pcec
            else:
                pcea += pcec
            pce_list.append(pcec)

        res = hc.calc_hazard_curves(groups, s_filter, imtls, gsims)
        # Compute samples of the Hermite polynomial
        csi = numpy.random.normal(loc=0.0, scale=1.0, size=num_samples)
        hercoef = get_hermite(csi)

        # Computing epistemic uncertainty using Monte Carlo
        std_epi = 0.047
        scaling_mc = numpy.random.normal(loc=0.0, scale=std_epi,
                                         size=num_samples_mc)
        hcmc = []
        for scl in scaling_mc:
            gsim = AbrahamsonEtAl2014NonErgodic(scaling_log=scl)
            gsims = {TRT.ACTIVE_SHALLOW_CRUST: gsim}
            res = hc.calc_hazard_curves(groups, s_filter, imtls, gsims)
            hcmc.append(-numpy.log(1.-res[key][0]))
        hcmc = numpy.array(hcmc)
        mean_mc = numpy.mean(hcmc, axis=0)
        std_mc = numpy.std(hcmc, axis=0)

        if PLOTTING:

            import matplotlib.pyplot as plt
            _ = plt.figure(figsize=(10, 8))

            curves = numpy.zeros((num_samples, len(imtls[key])))
            for rlz in range(0, num_samples):
                curves[rlz, :] = pcea[S, :, 0, 0]
                for deg in range(1, 5):
                    curves[rlz, :] += pcea[S, :, 0, deg] * hercoef[deg, rlz]
                if PLOTTING:
                    plt.plot(imtls[key], curves[rlz, :], ':', alpha=0.5,
                             color='grey')

            print(std_mc / numpy.std(curves, axis=0))

            plt.plot(imtls[key], pcea[0, :, 0, 0], '--sr', label='all', lw=4)
            plt.plot(imtls[key], pce_list[0][0, :, 0, 0], '--x', label='pce')
            tmp = - numpy.log(1.-res[key][0])
            plt.plot(imtls['SA(0.01)'], tmp, ':o', label='standard')
            plt.xscale('log')
            plt.yscale('log')
            plt.xlabel('IMLs')
            plt.ylabel('PoE')
            plt.grid(which='both')
            plt.show()
