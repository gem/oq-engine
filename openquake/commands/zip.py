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
import logging
from openquake.baselib import sap
from openquake.commonlib import oqzip


@sap.Script
def zip(what, archive_zip='', risk_ini=''):
    logging.basicConfig(level=logging.INFO)
    if os.path.basename(what) == 'ssmLT.xml':
        oqzip.zip_source_model(what, archive_zip)
    elif what.endswith('.xml'):  # assume exposure
        oqzip.zip_exposure(what, archive_zip)
    elif what.endswith('.ini'):  # a job.ini
        oqzip.zip_job(what, archive_zip, risk_ini)
    else:
        sys.exit('Cannot zip %s' % what)


zip.arg('what', 'path to a job.ini or a ssmLT.xml file')
zip.arg('archive_zip', 'path to a non-existing .zip file')
zip.opt('risk_ini', 'optional .ini file for risk')
