# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2026 GEM Foundation
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
import logging
from unittest import mock

from openquake.hazardlib import nrml
from openquake.risklib import read_nrml  # noqa
from openquake.risklib.asset import Exposure
from openquake.engine import engine


def main(fnames):
    """
    Check the validity of job.ini files, job.zip files and .xml files.
    """
    if os.environ.get('OQ_DISTRIBUTE') not in ('no', 'processpool'):
        os.environ['OQ_DISTRIBUTE'] = 'processpool'
    inis = []
    tomls = []
    for fname in fnames:
        if fname.endswith('.xml'):
            node = nrml.to_python(fname)
            if node.tag.endswith('exposureModel'):
                err = Exposure.check(fname)
                if err:
                    logging.warning(err)
            else:
                logging.info('Checked %s', fname)
        elif fname.endswith(('.ini', '.zip')):
            inis.append(fname)
        elif fname.endswith('.toml'):
            tomls.append(fname)
    with mock.patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
        if inis:
            engine.run_jobs(engine.create_jobs(inis))
        elif tomls:
            engine.run_workflow("check_input", tomls)

main.fnames = dict(help='File names to check', nargs='+')
