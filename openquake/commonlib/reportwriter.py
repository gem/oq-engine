# 2015.06.26 13:21:50 CEST
"""
Utilities to build a report writer generating a .rst report for a calculation
"""
from __future__ import print_function
import os

from openquake.commonlib import readinput, datastore
from openquake.calculators import base, views
from openquake.commonlib.oqvalidation import OqParam


def indent(text):
    return '  ' + '\n  '.join(text.splitlines())


class ReportWriter(object):
    """
    A particularly smart view over the datastore
    """
    title = dict(
        params='Parameters',
        inputs='Input files',
        csm_info='Composite source model',
        rupture_collections='Non-empty rupture collections',
        col_rlz_assocs='Collections <-> realizations',
        rlzs_assoc='Realizations per (TRT, GSIM)',
        data_transfer='Expected data transfer for the sources'
    )

    def __init__(self, dstore):
        description = OqParam.from_(dstore.attrs).description
        self.dstore = dstore
        self.text = description + '\n' + '=' * len(description)

    def add(self, name, obj=None):
        """Add the view named `name` to the report text"""
        title = self.title[name]
        line = '-' * len(title)
        if obj:
            text = '\n::\n\n' + indent(str(obj))
        else:
            orig = views.rst_table.__defaults__
            views.rst_table.__defaults__ = (None, '%s')  # disable formatting
            text = datastore.view(name, self.dstore)
            views.rst_table.__defaults__ = orig
        self.text += '\n'.join(['\n\n' + title, line, text])

    def save(self, fname):
        """Save the report"""
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
    calc.save_params()
    ds = datastore.DataStore(calc.datastore.calc_id)
    rw = ReportWriter(ds)
    report = os.path.join(output_dir, 'report.rst')
    for name in ('params', 'inputs'):
        rw.add(name)
    if 'scenario' not in oq.calculation_mode:
        rw.add('csm_info')
    rw.add('rlzs_assoc', calc.rlzs_assoc)
    if 'num_ruptures' in ds:
        rw.add('rupture_collections')
        rw.add('col_rlz_assocs')
    if oq.calculation_mode in ('classical', 'event_based', 'event_based_risk'):
        rw.add('data_transfer')
    rw.save(report)
    return report


def main(directory):
    for cwd, dirs, files in os.walk(directory):
        for f in files:
            if f in ('job.ini', 'job_h.ini', 'job_haz.ini', 'job_hazard.ini'):
                job_ini = os.path.join(cwd, f)
                print(job_ini)
                build_report(job_ini)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
