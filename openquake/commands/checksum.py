# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
import unittest.mock as mock
import os.path
from openquake.commonlib import readinput, datastore


def main(thing):
    """
    Get the checksum of a calculation from the calculation ID (if already
    done) or from the job.ini/job.zip file (if not done yet). If `thing`
    is a source model logic tree file, get the checksum of the model by
    ignoring the job.ini, the gmpe logic tree file and possibly other files.
    """
    try:
        job_id = int(thing)
        job_file = None
    except ValueError:
        job_id = None
        job_file = thing
        if not os.path.exists(job_file):
            sys.exit('%s does not correspond to an existing file' % job_file)
    if job_id:
        dstore = datastore.read(job_id)
        checksum = dstore['/'].attrs['checksum32']
    elif job_file.endswith('.xml'):  # assume it is a smlt file
        inputs = {'source_model_logic_tree': job_file}
        checksum = readinput.get_checksum32(
            mock.Mock(inputs=inputs, random_seed=42))
    else:
        oq = readinput.get_oqparam(job_file)
        checksum = readinput.get_checksum32(oq)
    print(checksum)


main.thing = 'job.ini, job.zip, job ID, smlt file'
