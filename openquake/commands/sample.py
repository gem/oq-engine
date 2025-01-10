#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2025 GEM Foundation
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

import json
import shutil
import numpy
import pandas
from openquake.hazardlib import (
    valid, nrml, sourceconverter, sourcewriter, logictree)
from openquake.baselib import general


def save_bak(fname, node, num_nodes, total):
    shutil.copy(fname, fname + '.bak')
    print('Copied the original file in %s.bak' % fname)
    with open(fname, 'wb') as f:
        nrml.write(node, f, xmlns=node['xmlns'])
    print('Extracted %d nodes out of %d' % (num_nodes, total))


def reduce_source_model(fname, reduction_factor, itime):
    """
    Reduce the source model by sampling the sources; as a special case,
    multiPointSources are split in pointSources and then sampled.
    """
    conv = sourceconverter.SourceConverter(area_source_discretization=20.,
                                           investigation_time=itime)
    [smodel] = nrml.read_source_models([fname], conv)
    grp = smodel.src_groups[0]
    if any(src.code == b'M' for src in grp):  # multiPoint
        for src in grp:
            if src.code == b'M':
                grp.sources = general.random_filter(src, reduction_factor)
                print('Extracted %d point sources out of %d' %
                      (len(grp), len(src)))
                break
    elif any(src.code == b'F' for src in grp):  # multiFault
        for src in grp:
            if src.code == b'F':
                rids = numpy.arange(src.count_ruptures())
                ok = general.random_filter(rids, reduction_factor)
                src.mags = src.mags[ok]
                src.rakes = src.rakes[ok]
                src.probs_occur = src.probs_occur[ok]
                src._rupture_idxs = [src._rupture_idxs[o] for o in ok]
                print('Extracted %d ruptures out of %d' %
                      (len(ok), len(rids)))
                break
    else:
        total = len(grp)
        grp.sources = general.random_filter(grp, reduction_factor)
        print('Extracted %d nodes out of %d' % (len(grp), total))
    smodel.src_groups = [grp]
    shutil.copy(fname, fname + '.bak')
    print('Copied the original file in %s.bak' % fname)
    sourcewriter.write_source_model(fname, smodel)


def main(fname, reduction_factor: valid.probability,
         investigation_time: valid.positivefloat = 50.):
    """
    Produce a submodel from `fname` by sampling the nodes randomly.
    Supports source models, site models and exposure models. As a special
    case, it is also able to reduce .csv files by sampling the lines.
    This is a debugging utility to reduce large computations to small ones.
    """
    if fname.endswith('.json'):  # used to sample the USGS stations
        with open(fname) as f:
            data = json.load(f)
        data['features'] = general.random_filter(data['features'], reduction_factor)
        with open(fname, 'w') as f:
            json.dump(data, f)
        return
    elif fname.endswith('.csv'):
        df = pandas.read_csv(fname, dtype=str)
        idxs = general.random_filter(numpy.arange(len(df)), reduction_factor)
        shutil.copy(fname, fname + '.bak')
        print('Copied the original file in %s.bak' % fname)
        df.loc[idxs].to_csv(fname, index=False,
                            lineterminator='\r\n', na_rep='nan')
        print('Extracted %d lines out of %d' % (len(idxs), len(df)))
        return
    elif fname.endswith('.npy'):
        array = numpy.load(fname)
        shutil.copy(fname, fname + '.bak')
        print('Copied the original file in %s.bak' % fname)
        arr = numpy.array(general.random_filter(array, reduction_factor))
        numpy.save(fname, arr)
        print('Extracted %d rows out of %d' % (len(arr), len(array)))
        return
    elif fname.endswith('_test.py'):
        # tests are not installed, so this import cannot stay at top-level
        from openquake.hazardlib.tests.gsim.utils import reduce_gsim_test
        print(reduce_gsim_test(fname, reduction_factor))
        return
    node = nrml.read(fname)
    model = node[0]
    if model.tag.endswith('exposureModel'):
        total = len(model.assets)
        model.assets.nodes = general.random_filter(
            model.assets, reduction_factor)
        num_nodes = len(model.assets)
    elif model.tag.endswith('siteModel'):
        total = len(model)
        model.nodes = general.random_filter(model, reduction_factor)
        num_nodes = len(model)
    elif model.tag.endswith('sourceModel'):
        reduce_source_model(fname, reduction_factor, investigation_time)
        return
    elif model.tag.endswith('logicTree'):
        for smpath in logictree.collect_info(fname).smpaths:
            reduce_source_model(smpath, reduction_factor, investigation_time)
        return
    else:
        raise RuntimeError('Unknown model tag: %s' % model.tag)
    save_bak(fname, node, num_nodes, total)


main.fname = 'path to the model file'
main.reduction_factor = 'reduction factor in the range 0..1'
main.investigation_time = 'investigation_time used in read_source_models'
