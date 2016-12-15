from __future__ import print_function
import numpy
from openquake.baselib import sap, hdf5


def convert_npz_hdf5(input_file, output_file):
    with hdf5.File(output_file, 'w') as out:
        with numpy.load(input_file) as inp:
            for key in inp:
                out[key] = inp[key]
    return output_file


@sap.Script
def to_hdf5(input):
    """
    Convert .npz files to .hdf5 files.
    """
    for input_file in input:
        if input_file.endswith('.npz'):
            output = convert_npz_hdf5(input_file, input_file[:-3] + 'hdf5')
            print('Generated %s' % output)

to_hdf5.arg('input', '.npz file to convert', nargs='*')
