import os
import unittest

from openquake.hazardlib.const import TRT
from openquake.baselib.general import DictArray
from openquake.hazardlib.calc.filters import SourceFilter

import openquake.hazardlib.calc.hazard_curve_ne as hcne
import openquake.hazardlib.calc.hazard_curve as hc
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
        rup = Dummy.get_rupture(mag=6.0)
        sfc = rup.surface
        rake = 90.
        self.src = CharacteristicFaultSource(id, nme, trt, mfd, tom, sfc, rake)
        # Creating the sites
        self.sitesc = Dummy.get_site_collection(2, hyp_lon=0.05, hyp_lat=0.25,
                                                vs30=500., vs30measured=True,
                                                z1pt0=50.)

    def test_kuehn2019ne(self):
        gsims = {TRT.ACTIVE_SHALLOW_CRUST: AbrahamsonEtAl2014NonErgodic()}

        from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008
        gsims = {TRT.ACTIVE_SHALLOW_CRUST: BooreAtkinson2008()}

        s_filter = SourceFilter(self.sitesc, {TRT.ACTIVE_SHALLOW_CRUST: 100.})
        groups = [self.src, self.src]
        imtls = {'SA(0.01)': [0.01, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4]}

        """
        pce_list = []
        for i, pcec in enumerate(hcne.calc_hazard_curves(groups, s_filter,
                                                         imtls, gsims)):
            if i == 0:
                pcea = pcec
            else:
                pcea += pcec
            pce_list.append(pcec)
        """

        res = hc.calc_hazard_curves(groups, s_filter, imtls, gsims)

        if True:
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(10, 8))
            # import pdb; pdb.set_trace()
            """
            plt.plot(imtls['SA(0.01)'], pcea[0, :, 0, 0],
                     'sr', label='all', lw=3)
            plt.plot(imtls['SA(0.01)'], pce_list[0][0, :, 0, 0],
                     '--x', label='pce')
            """
            plt.plot(imtls['SA(0.01)'], res['SA(0.01)'][0],
                     '-o', label='standard')
            print(res)

            plt.xscale('log')
            plt.yscale('log')
            plt.xlabel('IMLs')
            plt.ylabel('PoE')
            plt.grid(which='both')
            plt.show()
