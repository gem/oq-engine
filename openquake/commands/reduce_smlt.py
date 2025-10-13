#!/usr/bin/env python3
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
import os
import logging
from openquake.baselib.general import group_array
from openquake.hazardlib.logictree import SourceModelLogicTree, nrml


def main(smlt_path, src_id):
    """
    Reduce source model logic tree file and associated source mode files
    to the given source
    """
    # reduce the logic tree file
    smlt = SourceModelLogicTree(smlt_path).reduce(src_id)
    ltnode = smlt.to_node()
    redpath = 'reduced/' + smlt_path[len(smlt.basepath):]
    logging.info('Creating %s', redpath)
    if not os.path.exists('reduced'):
        os.mkdir('reduced')
    with open(redpath, 'wb') as f:
        nrml.write([ltnode], f)

    # reduce the source model files
    dic = group_array(smlt.source_data, 'fname')
    for path, array in dic.items():
        redpath = 'reduced/' + path
        logging.info('Creating %s', redpath)
        if not os.path.exists(os.path.dirname(redpath)):
            os.makedirs(os.path.dirname(redpath))
        sm = nrml.read(os.path.join(smlt.basepath, path)).sourceModel
        for grp in sm:
            grp.nodes = [src for src in grp if src['id'] in array['source']]
        with open(redpath, 'wb') as f:
            nrml.write([sm], f)

main.smlt_path = 'Path to a source model logic tree file'
main.src_id = 'Source ID'
