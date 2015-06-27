# 2015.06.26 13:21:50 CEST
"""
Utilities to build a report writer generating a .rst report for a calculation
"""

import os
from openquake.commonlib import readinput, datastore
from openquake.commonlib.calculators import base


def build_report(job_ini):
    oq = readinput.get_oqparam(job_ini)
    calc = base.calculators(oq)
    calc.pre_execute()
    ds = datastore.DataStore(calc.datastore.calc_id)
    report = os.path.join(os.path.dirname(job_ini), 'report.rst')
    with open(report, 'w') as f:
        f.write(datastore.view('csm_info', ds))


def main(directory):
    for cwd, dirs, files in os.walk(directory):
        for f in files:
            if f == 'job.ini':
                job_ini = os.path.join(cwd, f)
                print job_ini
                build_report(job_ini)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
