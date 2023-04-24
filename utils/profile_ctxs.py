# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import os
import logging
import cProfile
from openquake.baselib import general, performance, sap
from openquake.hazardlib.contexts import get_cmakers
from openquake.commonlib import readinput, datastore
from openquake.calculators.views import text_table


def build_ctxs(cmakers, src_groups, sitecol):
    for cmaker, sg in zip(cmakers, src_groups):
        srcs = []
        for src in sg:
            srcs.extend(src)
        ss = os.environ.get('OQ_SAMPLE_SOURCES')
        if ss:
            srcs = general.random_filter(srcs, float(ss)) or [srcs[0]]
        logging.info('Processing %d sources', len(srcs))
        cmaker.from_srcs(srcs, sitecol)


def main(job_ini):
    """
    Profile building the contexts. Use it as

    $ OQ_SAMPLE_SOURCES=.001 python profile_ctxs.py /path/to/job.ini

    This is  meant to be used on single site models. If you have many sites set
    something like OQ_SAMPLE_SITES=.0001 too.
    """
    logging.basicConfig(level=logging.INFO)
    with datastore.hdf5new() as h5:
        prof = cProfile.Profile()
        pstat = h5.filename + '.pstat'
        oq = readinput.get_oqparam(job_ini)
        csm = readinput.get_composite_source_model(oq, h5)
        sitecol = readinput.get_site_collection(oq)
        logging.info(sitecol)
        cmakers = get_cmakers(csm.src_groups, csm.full_lt, oq)
        logging.info('Storing performance info in %s', pstat)
        prof.runctx('build_ctxs(cmakers, csm.src_groups, sitecol)',
                    globals(), locals())
        prof.dump_stats(pstat)
    data = performance.get_pstats(pstat, n=60)
    print(text_table(data, ['ncalls', 'cumtime', 'path'], ext='org'))


main.job_ini = 'path to a job.ini file'

if __name__ == '__main__':
    sap.run(main)
