# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
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
from openquake.hazardlib import nrml
from openquake.hazardlib.calc.filters import magdepdist
from openquake.hazardlib.calc.stochastic import sample_ruptures

aae = numpy.testing.assert_almost_equal
HERE = pathlib.Path(__file__).parent


def _get_model_nankai():

    # source model for the Nankai region provided by M. Pagani
    source_model = HERE / 'data' / 'nankai' / 'nankai.xml'
    # it has a single group containing 15 mutex sources
    [group] = nrml.to_python(source_model)
    for i, src in enumerate(group):
        src.id = i
        src.grp_id = 0
        src.trt_smr = 0
        src.num_ruptures = src.count_ruptures()
    aae([src.mutex_weight for src in group],
        [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
         0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
    param = dict(ses_per_logic_tree_path=10, ses_seed=42, imtls={},
                 magdist=magdepdist())

    return group, param



class StochasticEventSetTestCase(unittest.TestCase):

    def test_nankai_a(self):

        # We generate 10 * 1 stochastic event sets each one of a duration of
        # one year. Since the source are mutually exclusive, we expect ten
        # realisations each one with a number of (independent) ruptures varying
        # between 1 and the maximum number admitted by each source. The fact
        # that the number of sources sampled corresponds to the number of
        # realisations stands in the fact that the 'grp_probability' is equal
        # to 1.
        # This means that the total number of ruptures must be equal or greater
        # than the 'ses_per_logic_tree_path' times
        # 'number_of_logic_tree_samples' i.e. the number of samples of the
        # investigation time for which we generate a stochastic event set

        # read the .xml with the source and set calc parameters
        group, param = _get_model_nankai()

        # Sample ruptures
        dic = sum(sample_ruptures(group, param), {})

        # This tests the number of ruptures
        self.assertEqual(len(dic['rup_array']), 8)

        # This checks the number of keys
        self.assertEqual(len(dic['source_data']), 6)

        # This checks the number of ruptures
        self.assertEqual(numpy.sum(dic['rup_array'].array['n_occ']), 13)

        # Test no filtering
        ruptures = sum(sample_ruptures(group, param), {})['rup_array']


    def test_nankai_b(self):

        # As previous but now we set the group probability to 0.7, meaning that
        # for 70% of the realisations we sample a source i.e. we generate
        # ruptures

        # read the .xml with the source and set calc parameters
        group, param = _get_model_nankai()
        group.grp_probability = 0.7
        param['ses_per_logic_tree_path'] = 100000

        # Sample ruptures
        dic = sum(sample_ruptures(group, param), {})

        # This tests the number of ruptures (not the number of occurrences).
        # 19 is indeed the number of unique rutpures that can be generated
        # by the sources in the group
        self.assertEqual(len(dic['rup_array']), 19)

        # This checks the number of ruptures. All the sources but four generate
        # generate up to 1 rupture. The other sources can generate up to 2
        # ruptures.
        # From 100,000 attempts we get 70,000 samples (checked in
        # stochastic.py).
        # The average number of ruptures per realization corresponds to the
        # the mean rate of ruptures generated per source (all 1 but the last
        # four, which have 1.5) times the 'srcs_weights'. This corresponds to
        # 1.25

        n_eqks = numpy.sum(dic['rup_array'].array['n_occ'])
        self.assertAlmostEqual(numpy.abs(n_eqks/int(70000*1.25)), 1.0, places=2)
