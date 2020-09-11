import sys
import logging
from openquake.baselib import parallel
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.commonlib import readinput


def main(job_ini):
    logging.basicConfig(level=logging.INFO)
    oq = readinput.get_oqparam(job_ini)
    sitecol = readinput.get_site_collection(oq)
    src_filter = SourceFilter(sitecol, oq.maximum_distance)
    csm = readinput.get_composite_source_model(oq)
    for eri, rlzs in csm.full_lt.get_rlzs_by_eri().items():
        groups = csm.get_groups(eri)
        for rlz in rlzs:
            hcurves = calc_hazard_curves(
                groups, src_filter, oq.imtls,
                csm.full_lt.gsim_by_trt(rlz),
                oq.truncation_level,
                parallel.Starmap.apply)
            print('rlz=%s, hcurves=%s' % (rlz, hcurves))
    parallel.Starmap.shutdown()


if __name__ == '__main__':
    main(sys.argv[1])  # path to a job.ini file
