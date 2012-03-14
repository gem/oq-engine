# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import h5py
import numpy
import os
import unittest
import shutil

from nose.plugins.attrib import attr

from openquake.db.models import OqJob

from tests.utils import helpers


DISAGG_DEMO_CONFIG = helpers.demo_file('disaggregation/config.gem')
EXPECTED_RESULTS_DIR = helpers.demo_file('disaggregation/expected_results')
EXPECTED_XML_FILE = os.path.join(EXPECTED_RESULTS_DIR,
                                 'disagg-results-sample:1-PoE:0.1.xml')

NFS_BASE_DIR = '/tmp'
XML_OUTPUT_DIR = os.path.join(os.path.dirname(DISAGG_DEMO_CONFIG),
                              'computed_output')
XML_OUTPUT_FILE = os.path.join(XML_OUTPUT_DIR,
                                 'disagg-results-sample:1-PoE:0.1.xml')
H5_OUTPUT_DIR = os.path.join(NFS_BASE_DIR, 'disagg-results', 'job-%s')
H5_OUTPUT_FILE = os.path.join(
    H5_OUTPUT_DIR,
    'disagg-results-sample:1-gmv:0.2259803-lat:0.0000000-lon:0.0000000.h5')

# number of tectonic region types
NTRT = 5


def read_data_values(path):
    """Read an expected results .dat file and return 1D array of rate
    values. (The .dat files are simple space-delimited text files; the
    values we want are in the last column position.)"""
    return [float(line.split()[-1]) for line in open(path, 'r')]


def subset_shape(subset_type, nlat, nlon, nmag, ndist, neps):
    """Get a tuple of dimenions which can be used to reshape a
    flattened version of a matrix."""
    subset_shapes = {
        'MagPMF': (nmag,),
        'DistPMF': (ndist,),
        'TRTPMF': (NTRT,),
        'MagDistPMF': (nmag, ndist),
        'MagDistEpsPMF': (nmag, ndist, neps),
        'LatLonPMF': (nlat, nlon),
        'LatLonMagPMF': (nlat, nlon, nmag),
        'LatLonMagEpsPMF': (nlat, nlon, nmag, neps),
        'MagTRTPMF': (nmag, NTRT),
        'LatLonTRTPMF': (nlat, nlon, NTRT),
        'FullDisaggMatrix': (nlat, nlon, nmag, neps, NTRT),
    }
    return subset_shapes[subset_type]


class DisaggCalcQATestCase(unittest.TestCase, helpers.ConfigTestCase):
    def setUp(self):
        super(DisaggCalcQATestCase, self).setUp()
        self.setup_config()
        os.environ.update(self.orig_env)
        cp = ConfigParser.SafeConfigParser()
        cp.read('openquake.cfg.test_bakk')
        cp.set('nfs', 'base_dir', NFS_BASE_DIR)
        cp.write(open('openquake.cfg', 'w'))

    def tearDown(self):
        super(DisaggCalcQATestCase, self).tearDown()
        self.teardown_config()
        shutil.rmtree(XML_OUTPUT_DIR)

    @attr('qa')
    def test_disagg(self):
        helpers.run_job(DISAGG_DEMO_CONFIG)

        job_record = OqJob.objects.latest("id")
        self.assertEqual('succeeded', job_record.status)

        self.assertTrue(os.path.exists(XML_OUTPUT_FILE))
        self._verify_xml_output(EXPECTED_XML_FILE, XML_OUTPUT_FILE,
                                job_record.id)

        h5_file = H5_OUTPUT_FILE % job_record.id
        self.assertTrue(os.path.exists(h5_file))
        self._verify_h5(h5_file, job_record.profile())

        # clean up the job hdf5 results dir:
        shutil.rmtree(H5_OUTPUT_DIR % job_record.id)

    def _verify_xml_output(self, expected, actual, job_id):
        """Read both `expected` and `actual` file and check for exact equality.
        """
        job_id_mapping = dict(job_id=job_id)

        # sanity checks: do the files exist?
        self.assertTrue(os.path.exists(expected))
        self.assertTrue(os.path.exists(actual))

        expected_text = open(expected, 'r').readlines()
        actual_text = open(actual, 'r').readlines()

        # sanity check; does it contain anything?
        self.assertTrue(len(expected_text) > 0)

        self.assertEqual(len(expected_text), len(actual_text))

        for i, line in enumerate(expected_text):
            if '%(job_id)s' in line:
                self.assertEqual(line % job_id_mapping,
                                 actual_text[i] % job_id_mapping)
            else:
                self.assertEqual(line, actual_text[i])

    def _verify_h5(self, h5_file, oq_job_profile):
        """Verify the contents of the resulting h5 file.

        :param h5_file:
            Path to the resulting h5 file.
        :param oq_job_profile:
            :class:`openquake.db.models.OqJobProfile` instance. We need this to
            access subset types and bin limits.
        """
        subset_types = oq_job_profile.disagg_results
        self.assertTrue(len(subset_types) > 0)

        nlat = len(oq_job_profile.lat_bin_limits) - 1
        nlon = len(oq_job_profile.lon_bin_limits) - 1
        ndist = len(oq_job_profile.distance_bin_limits) - 1
        nmag = len(oq_job_profile.mag_bin_limits) - 1
        neps = len(oq_job_profile.epsilon_bin_limits) - 1

        with h5py.File(h5_file, 'r') as h5:
            for subset in subset_types:
                dat_file = os.path.join(EXPECTED_RESULTS_DIR,
                                        '%s.dat' % subset)
                data = read_data_values(dat_file)
                shape = subset_shape(subset, nlat, nlon, nmag, ndist, neps)
                expected_matrix = numpy.reshape(data, shape)
                actual_matrix = h5[subset].value  # numpy.ndarray
                self.assertTrue(numpy.allclose(expected_matrix, actual_matrix))
