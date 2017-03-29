#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
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

from __future__ import print_function
import random
import shutil
from openquake.hazardlib import valid, nrml
from openquake.baselib.python3compat import encode
from openquake.baselib import sap


def random_filter(objects, reduction_factor, seed=42):
    """
    Given a list of objects, returns a sublist by extracting randomly
    some elements. The reduction factor (< 1) tells how small is the extracted
    list compared to the original list.
    """
    assert 0 < reduction_factor <= 1, reduction_factor
    rnd = random.Random(seed)
    out = []
    for obj in objects:
        if rnd.random() <= reduction_factor:
            out.append(obj)
    return out


@sap.Script
def reduce(fname, reduction_factor):
    """
    Produce a submodel from `fname` by sampling the nodes randomly.
    Supports source models, site models and exposure models. As a special
    case, it is also able to reduce .csv files by sampling the lines.
    This is a debugging utility to reduce large computations to small ones.
    """
    if fname.endswith('.csv'):
        with open(fname) as f:
            all_lines = f.readlines()
        lines = random_filter(all_lines, reduction_factor)
        shutil.copy(fname, fname + '.bak')
        print('Copied the original file in %s.bak' % fname)
        with open(fname, 'wb') as f:
            for line in lines:
                f.write(encode(line))
        print('Extracted %d lines out of %d' % (len(lines), len(all_lines)))
        return
    node = nrml.read(fname)
    model = node[0]
    if model.tag.endswith('exposureModel'):
        total = len(model.assets)
        model.assets.nodes = random_filter(model.assets, reduction_factor)
        num_nodes = len(model.assets)
    elif model.tag.endswith('siteModel'):
        total = len(model)
        model.nodes = random_filter(model, reduction_factor)
        num_nodes = len(model)
    elif model.tag.endswith('sourceModel'):
        total = len(model)
        model.nodes = random_filter(model, reduction_factor)
        num_nodes = len(model)
    else:
        raise RuntimeError('Unknown model tag: %s' % model.tag)
    shutil.copy(fname, fname + '.bak')
    print('Copied the original file in %s.bak' % fname)
    with open(fname, 'wb') as f:
        nrml.write([model], f, xmlns=node['xmlns'])
    print('Extracted %d nodes out of %d' % (num_nodes, total))

reduce.arg('fname', 'path to the model file')
reduce.arg('reduction_factor', 'reduction factor in the range 0..1',
           type=valid.probability)
