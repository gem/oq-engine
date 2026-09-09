# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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

import os
import time
from datetime import date, datetime, timedelta

from openquake.calculators.views import text_table
from openquake.commonlib import logs, datastore


def make_report(isodate='today'):
    """
    Build a Markdown report with the computations performed at the given
    isodate. Return the name of the report, saved in the current directory.
    """
    if isodate == 'today':
        isodate = date.today()
    else:
        isodate = date(*time.strptime(isodate, '%Y-%m-%d')[:3])
    isodate1 = isodate + timedelta(1)  # +1 day

    jobs = logs.dbcmd(
        'get_jobs_by_date', isodate.isoformat(), isodate1.isoformat())

    lines = ['# %d job(s) finished before midnight of %s\n' % (
        len(jobs), isodate)]

    # Add a summary of jobs
    for job_id, user, status, ds_calc in jobs:
        mark = '.' if status == 'complete' else '!'
        lines.append('* Job %s%s (%s)' % (job_id, mark, status))
    lines.append('\n---\n')

    for job_id, user, status, ds_calc in jobs:
        [stats] = logs.dbcmd('get_job_stats', job_id)
        (job_id, _user, _start_time, _stop_time, status, _duration) = stats
        try:
            ds = datastore.read(job_id, datadir=os.path.dirname(ds_calc))
            from openquake.calculators.reportwriter import ReportWriter
            report = ReportWriter(ds, fmt='md').make_report(show_inputs=False)
            title = ds['oqparam'].description
        except Exception as exc:
            report = 'Could not generate report: %s' % str(exc)
            title = 'Job %s' % job_id

        lines.append('## Job %s (%s) - %s\n' % (job_id, status, title))
        lines.append(text_table([[str(col) for col in stats]],
                                stats._fields, ext='md'))
        lines.append('\n' + report + '\n')
        lines.append('\n---\n')

    lines.append('Report last updated: %s\n' % datetime.now())
    page = '\n'.join(lines)
    fname = 'jobs-%s.md' % isodate
    with open(fname, 'w', encoding='utf8') as f:
        f.write(page)
    return fname
