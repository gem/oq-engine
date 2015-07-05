# 2015.06.26 13:21:50 CEST
"""
Utilities to build a report writer generating a .rst report for a calculation
"""

import os
from openquake.commonlib import readinput, datastore
from openquake.commonlib.calculators import base


class ReportBuilder(object):
    def __init__(self, dstore):
        description = dstore['oqparam'].description
        self.dstore = dstore
        self.title = dict(
            params='Parameters',
            inputs='Input files',
            csm_info='Composite source model',
            col_rlz_assocs='Collections <-> realizations',
        )
        self.text = description + '\n' + '=' * len(description)

    def add(self, name):
        title = self.title[name]
        line = '-' * len(title)
        self.text += '\n'.join(
            ['\n\n' + title, line, datastore.view(name, self.dstore)])
        
    def save(self, fname):
        with open(fname, 'w') as f:
            f.write(self.text)

                                     
def build_report(job_ini, output_dir=None):
    """
    Write a `report.csv` file with information about the calculation.

    :param job_ini:
        full pathname of the job.ini file
    :param output_dir:
        the directory where the report is written (default the input directory)
    """
    oq = readinput.get_oqparam(job_ini)
    output_dir = output_dir or os.path.dirname(job_ini)
    calc = base.calculators(oq)
    calc.pre_execute()
    ds = datastore.DataStore(calc.datastore.calc_id)
    rb = ReportBuilder(ds)
    report = os.path.join(output_dir, 'report.rst')
    for name in ('params', 'inputs'):
        rb.add(name)
    if 'scenario' not in oq.calculation_mode:
        rb.add('csm_info')
    if 'num_ruptures' in ds:
        rb.add('col_rlz_assocs')
    rb.save(report)


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
