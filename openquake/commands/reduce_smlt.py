#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2023 GEM Foundation
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
from openquake.hazardlib.logictree import SourceModelLogicTree, nrml


def main(smlt_path, src_id):
    """
    Reduce source model logic tree file and associated source mode files
    to the given source
    """
    # reduce the logic tree file
    smlt = SourceModelLogicTree(smlt_path)
    smlt.reduce(src_id)
    lt = nrml.read(smlt_path).logicTree
    for bset in lt:
        if bset['uncertaintyType'] not in {'sourceModel', 'extendModel'}:
            continue
        branches = []
        for br in bset:
            paths = (~br.uncertaintyModel).split()
            br.uncertaintyModel.text = ' '.join(
                p for p in paths if p in smlt.srcs_by_path)
            if br.uncertaintyModel.text and not branches:  # first time
                import pdb; pdb.set_trace()
                branches.append(br)
            elif branches:
                branches[0].uncertaintyWeight.text += br.uncertaintyWeight.text
        bset.nodes = branches
    lt.nodes = [bset for bset in lt.nodes if bset.nodes]
    if lt.nodes[0]['uncertaintyType'] == 'extendModel':
        # this happens if the source is in the extendModel files
        lt.nodes[0]['uncertaintyType'] = 'sourceModel'
    redpath = 'reduced/' + smlt_path
    logging.info('Creating %s', redpath)
    with open(redpath, 'wb') as f:
        nrml.write([lt], f)

    # reduce the source model files
    for path, srcs in smlt.srcs_by_path.items():
        redpath = 'reduced/' + path[len(smlt.basepath):]
        logging.info('Creating %s', redpath)
        if not os.path.exists(os.path.dirname(redpath)):
            os.makedirs(os.path.dirname(redpath))
        sm = nrml.read(path).sourceModel
        for grp in sm:
            grp.nodes = [src for src in grp if src['id'] in srcs]
        with open(redpath, 'wb') as f:
            nrml.write([sm], f)

main.smlt_path = 'Path to a source model logic tree file'
main.src_id = 'Source ID'
