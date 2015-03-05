#!/usr/bin/env python
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
    Produce a new exposure from `fname` by sampling the assets.
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
