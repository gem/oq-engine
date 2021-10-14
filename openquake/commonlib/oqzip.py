# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2021 GEM Foundation
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
import unittest.mock as mock
import os.path
import logging
from openquake.baselib import general
from openquake.risklib.asset import Exposure
from openquake.commonlib import readinput, logictree, oqvalidation


# useful for the mosaic files
def zip_all(directory):
    """
    Zip source models and exposures recursively
    """
    zips = []
    for cwd, dirs, files in os.walk(directory):
        if 'ssmLT.xml' in files:
            zips.append(zip_source_model(os.path.join(cwd, 'ssmLT.xml')))
        for f in files:
            if f.endswith('.xml') and 'exposure' in f.lower():
                zips.append(zip_exposure(os.path.join(cwd, f)))
    total = sum(os.path.getsize(z) for z in zips)
    logging.info('Generated %s of zipped data', general.humansize(total))


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


def zip_source_model(ssmLT, archive_zip='', log=logging.info):
    """
    Zip the source model files starting from the smmLT.xml file
    """
    basedir = os.path.dirname(ssmLT)
    if os.path.basename(ssmLT) != 'ssmLT.xml':
        orig = ssmLT
        ssmLT = os.path.join(basedir, 'ssmLT.xml')
        with open(ssmLT, 'wb') as f:
            f.write(open(orig, 'rb').read())

    archive_zip = archive_zip or os.path.join(basedir, 'ssmLT.zip')
    if os.path.exists(archive_zip):
        sys.exit('%s exists already' % archive_zip)
    info = logictree.collect_info(ssmLT)
    files = info.h5paths + info.smpaths
    oq = mock.Mock(inputs={'source_model_logic_tree': ssmLT},
                   random_seed=42, number_of_logic_tree_samples=0,
                   sampling_method='early_weights')
    oq._input_files = readinput.get_input_files(oq)
    checksum = readinput.get_checksum32(oq)
    checkfile = os.path.join(os.path.dirname(ssmLT), 'CHECKSUM.txt')
    with open(checkfile, 'w') as f:
        f.write(str(checksum))
    files.extend([os.path.abspath(ssmLT), os.path.abspath(checkfile)])
    general.zipfiles(files, archive_zip, log=log, cleanup=True)
    return archive_zip


def zip_exposure(exposure_xml, archive_zip='', log=logging.info):
    """
    Zip an exposure.xml file with all its .csv subfiles (if any)
    """
    archive_zip = archive_zip or exposure_xml[:-4] + '.zip'
    if os.path.exists(archive_zip):
        sys.exit('%s exists already' % archive_zip)
    [exp] = Exposure.read_headers([exposure_xml])
    files = [exposure_xml] + exp.datafiles
    general.zipfiles(files, archive_zip, log=log, cleanup=True)
    return archive_zip


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
