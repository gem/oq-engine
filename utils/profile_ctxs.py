# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2022, GEM Foundation
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
import logging
import cProfile
from openquake.baselib import performance, sap
from openquake.commonlib import readinput, datastore
from openquake.calculators.views import text_table


def extract(sources, redfactor):
    # reduce the number of sources to make the profiling fast
    split = []
    for src in sources:
        split.extend(src)
    return split[::redfactor]


def build_ctxs(cmakers, src_groups, sitecol, redfactor):
    for cmaker, sg in zip(cmakers, src_groups):
        srcs = extract(sg.sources, redfactor)
        logging.info('Processing %d sources', len(srcs))
        cmaker.from_srcs(srcs, sitecol)


def main(job_ini, redfactor: int):
    """
    Profile building the contexts. Use it as

    $ python profile_ctxs.py /path/to/job.ini reduction_factor

    A good value for the reduction factor could be 100, i.e. take one
    source (after split) every 100 sources. For large models increase
    the reduction factor to make the profiling reasonably fast.
    """
    logging.basicConfig(level=logging.INFO)
    with datastore.hdf5new() as h5:
        pstat = h5.filename + '.pstat'
        oq = readinput.get_oqparam(job_ini)
        csm = readinput.get_composite_source_model(oq, h5)
        sitecol = readinput.get_site_collection(oq)
        logging.info(sitecol)
        cmakers = csm._get_cmakers(oq)
        prof = cProfile.Profile()
        logging.info('Storing performance info in %s', pstat)
        prof.runctx('build_ctxs(cmakers, csm.src_groups, sitecol, redfactor)',
                    globals(), locals())
        prof.dump_stats(pstat)
        data = performance.get_pstats(pstat, n=60)
        print(text_table(data, ['ncalls', 'cumtime', 'path'], ext='org'))


main.job_ini = 'path to a job.ini file'
main.redfactor = 'reduction factor for the split sources'

if __name__ == '__main__':
    sap.run(main)
