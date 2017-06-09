from __future__ import print_function
import os
import logging
import numpy
from openquake.baselib import sap, hdf5, node, performance
from openquake.hazardlib import nrml


def convert_npz_hdf5(input_file, output_file):
    with hdf5.File(output_file, 'w') as out:
        with numpy.load(input_file) as inp:
            for key in inp:
                out[key] = inp[key]
    return output_file


def convert_xml_hdf5(input_file, output_file):
    with hdf5.File(output_file, 'w') as out:
        inp = nrml.read(input_file)
        if inp['xmlns'].endswith('nrml/0.4'):  # old version
            d = os.path.dirname(input_file) or '.'
            raise ValueError('Please upgrade with `oq upgrade_nrml %s`' % d)
        elif inp['xmlns'].endswith('nrml/0.5'):  # current version
            sm = inp.sourceModel
        else:  # not a NRML
            raise ValueError('Unknown NRML:' % inp['xmlns'])
        out.save(node.node_to_dict(sm))
    return output_file


@sap.Script
def to_hdf5(input):
    """
    Convert .xml and .npz files to .hdf5 files.
    """
    logging.basicConfig(level=logging.INFO)
    with performance.Monitor('to_hdf5') as mon:
        for input_file in input:
            if input_file.endswith('.npz'):
                output = convert_npz_hdf5(input_file, input_file[:-3] + 'hdf5')
            elif input_file.endswith('.xml'):  # for source model files
                output = convert_xml_hdf5(input_file, input_file[:-3] + 'hdf5')
            else:
                continue
            print('Generated %s' % output)
    print(mon)

to_hdf5.arg('input', '.npz file to convert', nargs='*')
