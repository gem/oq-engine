# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
import sys
import os.path
import logging
from openquake.baselib import general
from openquake.commonlib import readinput, oqvalidation


# useful for the mosaic
def zip_all(directory, ini):
    """
    Zip recursively a directory containing ini files
    """
    zips = []
    for cwd, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(ini):
                path = os.path.join(cwd, f)
                try:
                    oq = oqvalidation.OqParam(**readinput.get_params(path))
                except ValueError as exc:
                    print('skipping %s: %s' % (f, exc))
                    continue
                zips.extend(readinput.get_input_files(oq))
    total = sum(os.path.getsize(z) for z in zips)
    if os.path.exists('jobs.zip'):
        os.remove('jobs.zip')
    fname = general.zipfiles(zips, 'jobs.zip', log=logging.info)
    logging.info('Compressed %s -> %s of jobs.zip', general.humansize(total),
                 general.humansize(os.path.getsize(fname)))


# useful for the demos
def zip_all_jobs(directory):
    """
    Zip job.ini files recursively
    """
    zips = []
    for cwd, dirs, files in os.walk(directory):
        job_inis = [os.path.join(cwd, f) for f in sorted(files)
                    if f.endswith('.ini')]
        if not job_inis:
            continue
        elif len(job_inis) == 2:
            job_ini, risk_ini = job_inis
        else:
            [job_ini], risk_ini = job_inis, ''
        archive_zip = job_ini[:-4].replace('_hazard', '') + '.zip'
        zips.append(zip_job(job_ini, archive_zip, risk_ini))
        total = sum(os.path.getsize(z) for z in zips)
    logging.info('Generated %s of zipped data', general.humansize(total))


def zip_job(job_ini, archive_zip='', risk_ini='', oq=None, log=logging.info):
    """
    Zip the given job.ini file into the given archive, together with all
    related files.
    """
    if not os.path.exists(job_ini):
        sys.exit('%s does not exist' % job_ini)
    archive_zip = archive_zip or 'job.zip'
    if isinstance(archive_zip, str):  # actually it should be path-like
        if not archive_zip.endswith('.zip'):
            sys.exit('%s does not end with .zip' % archive_zip)
        if os.path.exists(archive_zip):
            sys.exit('%s exists already' % archive_zip)
    # do not validate to avoid permissions error on the export_dir
    oq = oq or oqvalidation.OqParam(**readinput.get_params(job_ini))
    if risk_ini:
        risk_ini = os.path.normpath(os.path.abspath(risk_ini))
        oqr = readinput.get_oqparam(
            risk_ini, kw=dict(hazard_calculation_id=1), validate=False)
        del oqr.inputs['job_ini']
        oq.inputs.update(oqr.inputs)
        oq.shakemap_uri.update(oqr.shakemap_uri)
    files = readinput.get_input_files(oq)
    if risk_ini:
        files = [risk_ini] + files
    return general.zipfiles(files, archive_zip, log=log)
