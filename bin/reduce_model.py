#!/usr/bin/env python
#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import random
import shutil
from openquake.commonlib import nrml
from openquake.commonlib import sap


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


def main(fname, reduction_factor):
    """
    Produce a submodel from `fname` by sampling the nodes randomly.
    This is a debugging utility to reduce large computations to small ones.
    """
    factor = float(reduction_factor)
    model, = nrml.read(fname)
    if model.tag.endswith('exposureModel'):
        total = len(model.assets)
        model.assets.nodes = random_filter(model.assets, factor)
        num_nodes = len(model.assets)
    elif model.tag.endswith('sourceModel'):
        total = len(model)
        model.nodes = random_filter(model, factor)
        num_nodes = len(model)
    else:
        raise RuntimeError('Unknown model tag: %s' % model.tag)
    shutil.copy(fname, fname + '~')
    print 'Copied the original file in %s~' % fname
    with open(fname, 'w') as f:
        nrml.write([model], f)
    print 'Extracted %d nodes out of %d' % (num_nodes, total)

if __name__ == '__main__':
    parser = sap.Parser(main)
    parser.arg('fname', 'path to the model file')
    parser.arg('reduction_factor', 'reduction factor in the range 0..1')
    parser.callfunc()
