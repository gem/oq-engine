# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018 GEM Foundation
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
import shutil
import logging
from openquake.baselib import sap
from openquake.commonlib import readinput
from openquake.hazardlib import nrml


class ObsoleteFormat(Exception):
    pass


@sap.Script
def renumber_sources(smlt_file):
    """
    Renumber the sources belowing to the same source model, even if split
    in multiple files, to avoid duplicated source IDs.
    """
    logging.basicConfig(level=logging.INFO)
    for paths in readinput.gen_sm_paths(smlt_file):
        number = 1
        for path in paths:
            # make a backup of the original file
            shutil.copy(path, path + '~')
            logging.info('Renumbering %s', path)
            root = nrml.read(path)
            if root['xmlns'] == 'http://openquake.org/xmlns/nrml/0.4':
                raise ObsoleteFormat('Please use oq upgrade_nrml .')
            [smodel] = root
            for sgroup in smodel:
                for src in sgroup:
                    src['id'] = str(number)
                    number += 1
            with open(path, 'wb') as f:
                nrml.write(root, f)

renumber_sources.arg('smlt_file', 'source model logic tree file')
