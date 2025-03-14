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
from openquake.calculators.checkers import check
from openquake.calculators.export import export

cd = pathlib.Path(__file__).parent


def check_export_job(dstore):
    fnames = [os.path.basename(f) for f in export(('job', 'zip'), dstore)]
    assert fnames == ['exposure.xml',
                      'assetcol.csv',
                      'job.ini',
                      'rupture.csv',
                      'gsim_logic_tree.xml',
                      'area_vulnerability.xml',
                      'contents_vulnerability.xml',
                      'nonstructural_vulnerability.xml',
                      'number_vulnerability.xml',
                      'occupants_vulnerability.xml',
                      'residents_vulnerability.xml',
                      'structural_vulnerability.xml',
                      'taxonomy_mapping.csv']


@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_impact(n):
    # NB: expecting exposure in oq-engine and not in mosaic_dir!
    if not os.path.exists(expo := cd.parent.parent.parent / 'exposure.hdf5'):
        raise unittest.SkipTest(f'Missing {expo}')
    calc = check(cd / f'impact{n}/job.ini', what='aggrisk_tags')
    if n == 1:
        check_export_job(calc.datastore)


def test_impact5():
    # this is a case where there are no assets inside the MMI multipolygons
    if not os.path.exists(expo := cd.parent.parent.parent / 'exposure.hdf5'):
        raise unittest.SkipTest(f'Missing {expo}')

    # importing the exposure around Nepal and aggregating it
    check(cd / 'impact5/job.ini')
