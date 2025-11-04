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

import unittest
import numpy
import pathlib

from openquake.hazardlib import nrml, contexts
from openquake.hazardlib.calc.stochastic import (
    sample_ruptures, sample_cluster)
from openquake.hazardlib.sourceconverter import SourceConverter
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
            src.trt_smr = 0
        aae([src.mutex_weight for src in group],
            [0.0125, 0.0125, 0.0125, 0.0125, 0.1625, 0.1625, 0.0125, 0.0125,
             0.025, 0.025, 0.05, 0.05, 0.325, 0.025, 0.1])
        param = dict(ses_per_logic_tree_path=10, ses_seed=42, imtls={})
        cmaker = contexts.ContextMaker('*', [SiMidorikawa1999SInter()], param)
        dic = sum(sample_ruptures(group, cmaker), {})
        self.assertEqual(len(dic['rup_array']), 8)
        self.assertEqual(len(dic['source_data']), 6)  # mutex sources

        # test no filtering
        ruptures = sum(sample_ruptures(group, cmaker), {})['rup_array']
        self.assertEqual(len(ruptures), 8)


class ClusterTestCase(unittest.TestCase):

    def setUp(self):
        self.sconv = SourceConverter(
            investigation_time=1.0,
            rupture_mesh_spacing=5.0,
            width_of_mfd_bin=0.1
        )

    def test_cluster(self):
        # In this case we use the source also used to test the calculation of
        # hazard using the classical approach and a simple cluster source

        # Source model file name
        ssm_fname = str(
            HERE / '..' / 'source_model' / 'source_group_cluster.xml')

        # Reading the SSM
        ssm = nrml.to_python(ssm_fname, self.sconv)

        # Generating the SESs
        ebrups = sample_cluster(ssm[0], 10000000, 1)

        # Computing the total number of occurrences
        tot_occ = 0
        for ebrup in ebrups:
            tot_occ += ebrup.n_occ

        # The rate of occurrence of the cluster is 1e-3 events per year and the
        # temporal occurrence model is Poissonian. This means that in a
        # simulation of 1M years we should have on average 1000 occurrences of
        # the cluster (and twice as many ruptures)
        ratio = 20000 / tot_occ
        numpy.testing.assert_almost_equal(ratio, 1.0, decimal=2)

    def test_src_mutex(self):
        # The rate of occurrence of the cluster is 0.1, the sources are
        # mutually exclusive (equally weighted) and ruptures independent. In
        # case of 1_000_000 samples of 1 year each, we expect on average
        # 100_000 occurences of the cluster. For each realization we sample one
        # source that will generate either with 1 or 2 ruptures. So the
        # total number of ruptures should be in the order of 150_000.

        # Source model file name
        ssm_fname = str(HERE / 'data' / 'ses_cluster' / 'ssm_mutex_indep.xml')

        # Reading
        ssm = nrml.to_python(ssm_fname, self.sconv)

        # Generating the SESs
        tot_occ = 0
        nrlz = 10
        for i in range(nrlz):

            ebrups = sample_cluster(ssm[0], 1000000, i)

            # Computing the total number of occurrences
            if ebrups is None:
                breakpoint()
                continue
            tot_occ += numpy.sum([e.n_occ for e in ebrups])

        # Checking the number of ruptures generated
        msg = 'The ratio between computed and expected ruptures exceeds 1%'
        self.assertTrue(numpy.abs(tot_occ / nrlz / 150000 - 1.0) < 0.01, msg)

    def test_src_indep(self):
        # Sources are independent and ruptures mutex. The rate of occurrence of
        # the cluster is 1/10. With 1_000_000 samples of 1 year each, we expect
        # on average 100_000 occurences of the cluster. For each realization we
        # sample either one or two sources that will generate 1 rupture. So the
        # total number of ruptures should be also in this case in the order of
        # 150_000.

        # Source model file name
        ssm_fname = str(HERE / 'data' / 'ses_cluster' / 'ssm_indep_mutex.xml')

        # Reading
        ssm = nrml.to_python(ssm_fname, self.sconv)

        # Generating the SESs
        tot_occ = 0
        nrlz = 10
        for i in range(nrlz):
            ebrups = sample_cluster(ssm[0], 1000000, i)

            # Computing the total number of occurrences
            tot_occ += numpy.sum([e.n_occ for e in ebrups])

        # Checking the number of ruptures generated
        msg = 'The ratio between computed and expected ruptures exceeds 1%'
        self.assertTrue(numpy.abs(tot_occ / nrlz / 150000 - 1.0) < 0.01, msg)
