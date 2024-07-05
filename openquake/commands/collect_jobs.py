# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024 GEM Foundation
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
import time
from openquake.commonlib import logs

def main(job_ids):
    """
    Wait for the given jobs to finish and then collect the results
    """
    while True:
        rows = logs.dbcmd('SELECT id, status FROM job WHERE id in (?X)', job_ids)
        failed = [row for row in rows if row.status == 'failed']
        if failed:
            sys.exit('Job %d failed' % failed[0])
        complete = [row for row in rows if row.status == 'complete']
        if len(complete) == len(rows):
            print('All jobs completed correctly')
            break
        time.sleep(30.)

main.job_ids = dict(help='number of jobs to create in the database', nargs='+')
