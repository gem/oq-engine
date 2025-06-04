# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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
import pathlib
import unittest
import pytest
import numpy
from openquake.calculators.base import expose_outputs
from openquake.calculators.checkers import check
from openquake.calculators.export import export

cd = pathlib.Path(__file__).parent
aac = numpy.testing.assert_allclose

def strip(fname):
    bname = os.path.basename(fname)
    name, ext = bname.rsplit('_', 1)
    return name + '.' + ext.rsplit('.')[1]


def check_export_job(dstore):
    fnames = export(('job', 'zip'), dstore)
    assert [strip(f) for f in fnames] == [
        'job.ini',
        'exposure.xml',
        'rupture.csv',
        'gsim_logic_tree.xml',
        'affectedpop_vulnerability.xml',
        'area_vulnerability.xml',
        'contents_vulnerability.xml',
        'injured_vulnerability.xml',
        'nonstructural_vulnerability.xml',
        'number_vulnerability.xml',
        'occupants_vulnerability.xml',
        'residents_vulnerability.xml',
        'structural_vulnerability.xml',
        'taxonomy_mapping.csv',
        'sites.csv',
        'assetcol.csv']
    # there is not gmfs_file, since this is a test without shakemap
    return fnames


def compare(dstore1, dstore2):
    """
    Compare avg_losses and loss_by_event
    """
    ltypes = sorted(dstore1['avg_losses-stats'])
    df1 = dstore1.read_df('loss_by_event')
    df2 = dstore2.read_df('loss_by_event')
    aac(df1.to_numpy(), df2.to_numpy(), rtol=1e-5)

    for ltype in ltypes:
        avg1 = dstore1[f'avg_losses-stats/{ltype}'][:]
        avg2 = dstore2[f'avg_losses-stats/{ltype}'][:]
        aac(avg1, avg2, rtol=1e-5)

# for the moment we are testing aggregate_by=ID_1 and not ID_2
@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_impact(n):
    # NB: expecting exposure in oq-engine and not in mosaic_dir!
    if not os.path.exists(expo := cd.parent.parent.parent / 'exposure.hdf5'):
        raise unittest.SkipTest(f'Missing {expo}')
    calc, log = check(cd / f'impact{n}/job.ini', what='aggrisk_tags')
    if n == 1:
        # repeat the calculation by exporting the input files
        fnames = check_export_job(calc.datastore)
        calc2, log2 = check(fnames[0])
        with log, log2:
            expose_outputs(calc.datastore)
            expose_outputs(calc2.datastore)
            compare(calc.datastore, calc2.datastore)

def test_impact5():
    # this is a case where there are no assets inside the MMI multipolygons
    if not os.path.exists(expo := cd.parent.parent.parent / 'exposure.hdf5'):
        raise unittest.SkipTest(f'Missing {expo}')

    # importing the exposure around Nepal and aggregating it
    check(cd / 'impact5/job.ini')
