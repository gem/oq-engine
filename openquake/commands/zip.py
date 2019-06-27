# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2019 GEM Foundation
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
from openquake.baselib import sap
from openquake.commonlib import oqzip


@sap.script
def zip(what, archive_zip='', risk_file=''):
    """
    Zip into an archive one or two job.ini files with all related files
    """
    if os.path.isdir(what):
        oqzip.zip_all(what)
    elif what.endswith('.xml') and '<logicTree' in open(what).read(512):
        # hack to see if the NRML file is of kind logicTree
        oqzip.zip_source_model(what, archive_zip)
    elif what.endswith('.xml') and '<exposureModel' in open(what).read(512):
        # hack to see if the NRML file is of kind exposureModel
        oqzip.zip_exposure(what, archive_zip)
    elif what.endswith('.ini'):  # a job.ini
        oqzip.zip_job(what, archive_zip, risk_file)
    else:
        sys.exit('Cannot zip %s' % what)


zip.arg('what', 'path to a job.ini, an ssmLT.xml, an exposure.xml, '
        'or to a directory containing a file ssmLT.xml')
zip.arg('archive_zip', 'path to a non-existing .zip file')
zip.opt('risk_file', 'optional file for risk')
