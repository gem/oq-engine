# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2018 GEM Foundation
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
import sys
import os.path
from openquake.baselib import sap, datastore
from openquake.commonlib import readinput


@sap.Script
def checksum(job_file_or_job_id):
    """
    Get the checksum of a calculation from the calculation ID (if already
    done) or from the job.ini/job.zip file (if not done yet).
    """
    try:
        job_id = int(job_file_or_job_id)
        job_file = None
    except ValueError:
        job_id = None
        job_file = job_file_or_job_id
        if not os.path.exists(job_file):
            sys.exit('%s does not correspond to an existing file' % job_file)
    if job_id:
        dstore = datastore.read(job_id)
        checksum = dstore['/'].attrs['checksum32']
    else:
        oq = readinput.get_oqparam(job_file)
        checksum = readinput.get_checksum32(oq)
    print(checksum)

checksum.arg('job_file_or_job_id', 'job.ini, job.zip or job ID')
