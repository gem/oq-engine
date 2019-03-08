# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2019 GEM Foundation
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
import os
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


@sap.script
def to_hdf5(input):
    """
    Convert .xml and .npz files to .hdf5 files.
    """    
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
