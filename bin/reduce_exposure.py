#!/usr/bin/env python
import random
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


def reduced_fname(fname, reduction_factor):
    """
    Build the name of the reduced model
    """
    assert fname.endswith('.xml'), fname
    return fname[:-4] + '_reduced_%s.xml' % reduction_factor


def main(exposure_fname, reduction_factor):
    """
    Produce a new exposure from `exposure_fname` by sampling the assets.
    """
    exposure = nrml.read(exposure_fname).exposureModel
    all_assets = len(exposure.assets)
    exposure.assets.nodes = random_filter(
        exposure.assets, float(reduction_factor))
    fname = reduced_fname(exposure_fname, reduction_factor)
    with open(fname, 'w') as f:
        nrml.write([exposure], f)
    print 'Extracted %d assets out of %d: %s' % (
        len(exposure.assets), all_assets, fname)

if __name__ == '__main__':
    parser = sap.Parser(main)
    parser.arg('exposure_fname', 'path to the exposure file')
    parser.arg('reduction_factor', 'reduction factor in the range 0..1')
    parser.callfunc()
