#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os.path
import logging
from openquake.baselib import general
from openquake.hazardlib import nrml
from openquake.commonlib import readinput, logictree


def zip_source_model(ssmLT, archive_zip='', log=logging.info):
    """
    Zip the source model files starting from the smmLT.xml file
    """
    basedir = os.path.dirname(ssmLT)
    archive_zip = archive_zip or os.path.join(basedir, 'ssmLT.zip')
    if os.path.exists(archive_zip):
        sys.exit('%s exists already' % archive_zip)
    files = [os.path.abspath(ssmLT)] + logictree.collect_info(ssmLT).smpaths
    general.zipfiles(files, archive_zip, log=log)


def zip_exposure(exposure_xml, archive_zip='', log=logging.info):
    """
    Zip an exposure.xml file with all its .csv subfiles (if any)
    """
    pass


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
    files = set()
    if risk_ini:
        risk_ini = os.path.normpath(os.path.abspath(risk_ini))
        oq.inputs.update(readinput.get_params([risk_ini])['inputs'])
        files.add(os.path.normpath(os.path.abspath(job_ini)))

    # collect .hdf5 tables for the GSIMs, if any
    if 'gsim_logic_tree' in oq.inputs or oq.gsim:
        gsim_lt = readinput.get_gsim_lt(oq)
        for gsims in gsim_lt.values.values():
            for gsim in gsims:
                table = getattr(gsim, 'GMPE_TABLE', None)
                if table:
                    files.add(table)

    # collect exposure.csv, if any
    exposures_xml = oq.inputs.get('exposure', [])
    for exposure_xml in exposures_xml:
        dname = os.path.dirname(exposure_xml)
        expo = nrml.read(exposure_xml, stop='asset')[0]
        if not expo.assets:
            exposure_csv = (~expo.assets).strip()
            for csv in exposure_csv.split():
                if csv and os.path.exists(os.path.join(dname, csv)):
                    files.add(os.path.join(dname, csv))

    # collection .hdf5 UCERF file, if any
    if oq.calculation_mode.startswith('ucerf_'):
        sm = nrml.read(oq.inputs['source_model'])
        fname = sm.sourceModel.UCERFSource['filename']
        f = os.path.join(os.path.dirname(oq.inputs['source_model']), fname)
        files.add(os.path.normpath(f))

    # collect all other files
    for key in oq.inputs:
        fname = oq.inputs[key]
        if isinstance(fname, list):
            for f in fname:
                files.add(os.path.normpath(f))
        elif isinstance(fname, dict):
            for f in fname.values():
                files.add(os.path.normpath(f))
        else:
            files.add(os.path.normpath(fname))
    general.zipfiles(files, archive_zip, log=log)
    logging.info('Generated %s', archive_zip)
