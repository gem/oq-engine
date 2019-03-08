#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import csv
import shutil
import numpy
from openquake.hazardlib import valid, nrml
from openquake.baselib.python3compat import encode
from openquake.baselib import sap, general
from openquake.commonlib import logictree


def _save_csv(fname, lines, header):
    with open(fname, 'wb') as f:
        if header:
            f.write(encode(header))
        for line in lines:
            f.write(encode(line))


def save_bak(fname, node, num_nodes, total):
    shutil.copy(fname, fname + '.bak')
    print('Copied the original file in %s.bak' % fname)
    with open(fname, 'wb') as f:
        nrml.write(node, f, xmlns=node['xmlns'])
    print('Extracted %d nodes out of %d' % (num_nodes, total))


def reduce_source_model(fname, reduction_factor):
    node = nrml.read(fname)
    if node['xmlns'] == 'http://openquake.org/xmlns/nrml/0.5':
        total = sum(len(sg) for sg in node[0])
        num_nodes = 0
        for sg in node[0]:
            sg.nodes = general.random_filter(sg, reduction_factor)
            num_nodes += len(sg)
    else:  # nrml/0.4
        total = len(node[0].nodes)
        node[0].nodes = general.random_filter(node[0], reduction_factor)
        num_nodes = len(node[0].nodes)
    save_bak(fname, node, num_nodes, total)


@sap.script
def reduce(fname, reduction_factor):
    """
    Produce a submodel from `fname` by sampling the nodes randomly.
    Supports source models, site models and exposure models. As a special
    case, it is also able to reduce .csv files by sampling the lines.
    This is a debugging utility to reduce large computations to small ones.
    """
    if fname.endswith('.csv'):
        with open(fname) as f:
            line = f.readline()  # read the first line
            if csv.Sniffer().has_header(line):
                header = line
                all_lines = f.readlines()
            else:
                header = None
                f.seek(0)
                all_lines = f.readlines()
        lines = general.random_filter(all_lines, reduction_factor)
        shutil.copy(fname, fname + '.bak')
        print('Copied the original file in %s.bak' % fname)
        _save_csv(fname, lines, header)
        print('Extracted %d lines out of %d' % (len(lines), len(all_lines)))
        return
    elif fname.endswith('.npy'):
        array = numpy.load(fname)
        shutil.copy(fname, fname + '.bak')
        print('Copied the original file in %s.bak' % fname)
        arr = numpy.array(general.random_filter(array, reduction_factor))
        numpy.save(fname, arr)
        print('Extracted %d rows out of %d' % (len(arr), len(array)))
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
        reduce_source_model(fname, reduction_factor)
        return
    elif model.tag.endswith('logicTree'):
        for smpath in logictree.collect_info(fname).smpaths:
            reduce_source_model(smpath, reduction_factor)
        return
    else:
        raise RuntimeError('Unknown model tag: %s' % model.tag)
    save_bak(fname, node, num_nodes, total)


reduce.arg('fname', 'path to the model file')
reduce.arg('reduction_factor', 'reduction factor in the range 0..1',
           type=valid.probability)
