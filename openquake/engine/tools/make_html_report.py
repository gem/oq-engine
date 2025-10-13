# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import html
import time
from datetime import date, datetime, timedelta
import itertools
from docutils.examples import html_parts

from openquake.calculators.views import view_fullreport, text_table
from openquake.commonlib import logs, datastore

tablecounter = itertools.count(0)


JOB_STATS = '''
SELECT id, user_name, start_time, stop_time, status,
strftime('%s', stop_time) - strftime('%s', start_time) AS duration
FROM job WHERE id=?x;
'''

ALL_JOBS = '''
SELECT id, user_name, status, ds_calc_dir FROM job
WHERE start_time >= ?x AND start_time < ?x ORDER BY stop_time
'''

PAGE_TEMPLATE = '''\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="http://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js">
</script>
<link rel="stylesheet"
 href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/themes/smoothness/jquery-ui.css"
/>
<script
 src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/jquery-ui.min.js">
</script>
<script>
$(function() {
$("#tabs").tabs();
});
</script>
</head>
<body>
%s
</body>
</html>
'''


def make_tabs(tag_ids, tag_status, tag_contents):
    """
    Return a HTML string containing all the tabs we want to display
    """
    templ = '''
<div id="tabs">
<ul>
%s
</ul>
%s
</div>'''
    lis = []
    contents = []
    for i, (tag_id, status, tag_content) in enumerate(
            zip(tag_ids, tag_status, tag_contents), 1):
        mark = '.' if status == 'complete' else '!'
        lis.append('<li><a href="#tabs-%d">%s%s</a></li>' % (i, tag_id, mark))
        contents.append('<div id="tabs-%d">%s</div>' % (
            i, tag_content))
    return templ % ('\n'.join(lis), '\n'.join(contents))


def make_report(isodate='today'):
    """
    Build a HTML report with the computations performed at the given isodate.
    Return the name of the report, which is saved in the current directory.
    """
    if isodate == 'today':
        isodate = date.today()
    else:
        isodate = date(*time.strptime(isodate, '%Y-%m-%d')[:3])
    isodate1 = isodate + timedelta(1)  # +1 day

    tag_ids = []
    tag_status = []
    tag_contents = []

    # the fetcher returns an header which is stripped with [1:]
    jobs = logs.dbcmd(
        'fetch', ALL_JOBS, isodate.isoformat(), isodate1.isoformat())
    page = '<h2>%d job(s) finished before midnight of %s</h2>' % (
        len(jobs), isodate)
    for job_id, user, status, ds_calc in jobs:
        tag_ids.append(job_id)
        tag_status.append(status)
        [stats] = logs.dbcmd('fetch', JOB_STATS, job_id)
        (job_id, _user, _start_time, _stop_time, status, _duration) = stats
        try:
            ds = datastore.read(job_id, datadir=os.path.dirname(ds_calc))
            txt = view_fullreport('fullreport', ds)
            report = html_parts(txt)
        except Exception as exc:
            report = dict(
                html_title='Could not generate report: %s' % html.escape(
                    str(exc), quote=True),
                fragment='')
        page = report['html_title']
        page += text_table([[str(col) for col in stats]],
                           stats._fields, ext='html')
        page += report['fragment']
        tag_contents.append(page)

    page = make_tabs(tag_ids, tag_status, tag_contents) + (
        'Report last updated: %s' % datetime.now())
    fname = 'jobs-%s.html' % isodate
    with open(fname, 'w') as f:
        f.write(PAGE_TEMPLATE % page)
    return fname
