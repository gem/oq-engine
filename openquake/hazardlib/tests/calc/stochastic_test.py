# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import unittest
import numpy
import pathlib

from openquake.hazardlib import nrml, contexts
from openquake.hazardlib.calc.stochastic import (
    sample_ruptures, sample_cluster)
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter

aae = numpy.testing.assert_almost_equal

HERE = pathlib.Path(__file__).parent


class StochasticEventSetTestCase(unittest.TestCase):

    def test_nankai(self):
        # source model for the Nankai region provided by M. Pagani

        # Source model file name
        # ssm_fname = os.path.join(os.path.dirname(__file__), 'nankai.xml')
        ssm_fname = HERE / 'data' / 'nankai' / 'nankai.xml'

        # It has a single group containing 15 mutex sources
        [group] = nrml.to_python(ssm_fname)
        for i, src in enumerate(group):
            src.id = i
            src.grp_id = 0
            src.num_ruptures = src.count_ruptures()
        aae([src.mutex_weight for src in group],
            [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
             0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
        param = dict(ses_per_logic_tree_path=10, ses_seed=42, imtls={})
        cmaker = contexts.ContextMaker('*', [SiMidorikawa1999SInter()], param)
        dic = sum(sample_ruptures(group, cmaker), {})
        self.assertEqual(len(dic['rup_array']), 7)
        self.assertEqual(len(dic['source_data']), 6)  # mutex sources

        # test no filtering
        ruptures = sum(sample_ruptures(group, cmaker), {})['rup_array']
        self.assertEqual(len(ruptures), 7)


class ClusterTestCase(unittest.TestCase):

    def test_src_mutex(self):
        # The rate of occurrence of the cluster is 1/1000, the sources are
        # mutually exclusive (equally weighted) and ruptures independent. In
        # case of 100_000 samples of 1 year each, we expect on average 100
        # occurences of the cluster either with 1 or 2 ruptures. So the
        # total number of ruptures should the in the order of 150.

        # Source model file name
        ssm_fname = str(HERE / 'data' / 'ses_cluster' / 'ssm01.xml')

        from openquake.hazardlib.sourceconverter import SourceConverter
        sconv = SourceConverter(
            investigation_time=1.0,
            rupture_mesh_spacing=5.0,
            width_of_mfd_bin=0.1
        )

        # Reading
        ssm = nrml.to_python(ssm_fname, sconv)

        # Generating the SESs
        ebrups = sample_cluster(ssm[0], 1000000, 1)

        # Computing the total number of occurrences
        tot_occ = 0
        for ebrup in ebrups:
            tot_occ += ebrup.n_occ
        print(tot_occ)

        breakpoint()

    def test_src_indep(self):
        # Sources are mutually exclusive and ruptures independent. The rate of
        # occurrence of the cluster is 1/1000, the sources are mutually exclusive (equally
        # weighted) and ruptures independent.

        pass
