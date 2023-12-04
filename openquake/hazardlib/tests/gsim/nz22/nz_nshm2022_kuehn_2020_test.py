
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.nz22.nz_nshm2022_kuehn_2020 import (
    NZNSHM2022_KuehnEtAl2020SInter,
    NZNSHM2022_KuehnEtAl2020SSlab
)


class NZNSHM2022KuehnEtAl2020RegionTestCase(BaseGSIMTestCase):
    FILES = [
        {
            "region": "NZL",
            "files": [
                "nz22/kuehn2020/KUEHN20_{}_NZL_GNS_MEAN.csv",
                "nz22/kuehn2020/KUEHN20_{}_NZL_GNS_TOTAL_STDDEV_ORIGINAL_SIGMA.csv"],
            "modified_sigma": False,
        },
        {
            "region": "NZL",
            "files": [
                "nz22/kuehn2020/KUEHN20_{}_NZL_GNS_MEAN.csv",
                "nz22/kuehn2020/KUEHN20_{}_NZL_GNS_TOTAL_STDDEV_MODIFIED_SIGMA.csv"],
            "modified_sigma": True,
        },
    ]

    def test_all(self):
        for gcls, trt in zip([NZNSHM2022_KuehnEtAl2020SInter, NZNSHM2022_KuehnEtAl2020SSlab],
                             ['INTERFACE', 'INSLAB']):
            self.GSIM_CLASS = gcls
            for test_case in self.FILES:
                region = test_case["region"]
                files = test_case["files"]
                modified_sigma = test_case["modified_sigma"]
                mean_file, *std_files = [f.format(trt) for f in files]
                self.check(mean_file,
                           max_discrep_percentage=0.03, region=region, modified_sigma=modified_sigma)
                self.check(*std_files,
                           max_discrep_percentage=0.03, region=region, modified_sigma=modified_sigma)
