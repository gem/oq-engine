# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import sys
import os.path
import logging
from openquake.baselib import sap, general
from openquake.commonlib import readinput


@sap.Script
def zip(job_ini, archive_zip):
    """
    Zip the given job.ini file into the given archive, together with all
    related files.
    """
    if not os.path.exists(job_ini):
        sys.exit('%s does not exist' % job_ini)
    if not archive_zip.endswith('.zip'):
        sys.exit('%s does not end with .zip' % archive_zip)
    if os.path.exists(archive_zip):
        sys.exit('%s exists already' % archive_zip)
    logging.basicConfig(level=logging.INFO)
    oq = readinput.get_oqparam(job_ini)

    # collect .hdf5 tables for the GSIMs, if any
    gsim_lt = readinput.get_gsim_lt(oq)
    gmpetables = set()
    for gsims in gsim_lt.values.values():
        for gsim in gsims:
            table = getattr(gsim, 'GMPE_TABLE', None)
            if table:
                gmpetables.add(table)

    # collect all other files
    files = list(gmpetables)
    for key in oq.inputs:
        fname = oq.inputs[key]
        if isinstance(fname, list):
            for f in fname:
                files.append(os.path.normpath(f))
        else:
            files.append(os.path.normpath(fname))
    general.zipfiles(files, archive_zip, log=logging.info)


zip.arg('job_ini', 'path to a job.ini file')
zip.arg('archive_zip', 'path to a non-existing .zip file')
