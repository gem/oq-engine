# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
import mock
import os.path
import logging
from openquake.baselib import general
from openquake.risklib.asset import Exposure
from openquake.commonlib import readinput, logictree


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
    oq = mock.Mock(inputs={'source_model_logic_tree': ssmLT})
    checksum = readinput.get_checksum32(oq)
    checkfile = os.path.join(os.path.dirname(ssmLT), 'CHECKSUM.txt')
    with open(checkfile, 'w') as f:
        f.write(str(checksum))
    files = [os.path.abspath(ssmLT), os.path.abspath(checkfile)]
    for fs in logictree.collect_info(ssmLT).smpaths.values():
        files.extend(fs)
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
    oq = oq or readinput.get_oqparam(job_ini, validate=False)
    if risk_ini:
        risk_ini = os.path.normpath(os.path.abspath(risk_ini))
        risk_inputs = readinput.get_params([risk_ini])['inputs']
        del risk_inputs['job_ini']
        oq.inputs.update(risk_inputs)
    files = readinput.get_input_files(oq)
    if risk_ini:
        files = [risk_ini] + files
    return general.zipfiles(files, archive_zip, log=log)
