# Copyright (c) 2010-2014, GEM Foundation.
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

import os.path
from qa_tests import _utils
from openquake.qa_tests_data.disagg import case_1, case_2


class DisaggHazardCase1TestCase(_utils.DisaggHazardTestCase):
    working_dir = os.path.dirname(case_1.__file__)
    imts = ['PGA', 'SA-0.025']
    fnames = [
        'disagg_matrix(0.02)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1.xml',
        'disagg_matrix(0.1)-lon_10.1-lat_40.1-smltp_b1-gsimltp_b1.xml',
    ]


class DisaggHazardCase2TestCase(_utils.DisaggHazardTestCase):
    working_dir = os.path.dirname(case_2.__file__)
    imts = ['PGA']
    fnames = '''\
disagg_matrix(0.02)-lon_0.0-lat_0.0-smltp_source_model_1-gsimltp_ChiouYoungs2008_YoungsEtAl1997SSlab.xml
disagg_matrix(0.02)-lon_0.0-lat_0.0-smltp_source_model_2-gsimltp_BooreAtkinson2008.xml
disagg_matrix(0.02)-lon_0.0-lat_0.0-smltp_source_model_2-gsimltp_ChiouYoungs2008.xml
disagg_matrix(0.02)-lon_-3.0-lat_-3.0-smltp_source_model_1-gsimltp_BooreAtkinson2008_YoungsEtAl1997SSlab.xml
disagg_matrix(0.02)-lon_-3.0-lat_-3.0-smltp_source_model_1-gsimltp_ChiouYoungs2008_YoungsEtAl1997SSlab.xml
disagg_matrix(0.1)-lon_0.0-lat_0.0-smltp_source_model_1-gsimltp_BooreAtkinson2008_YoungsEtAl1997SSlab.xml
disagg_matrix(0.1)-lon_0.0-lat_0.0-smltp_source_model_1-gsimltp_ChiouYoungs2008_YoungsEtAl1997SSlab.xml
disagg_matrix(0.1)-lon_0.0-lat_0.0-smltp_source_model_2-gsimltp_BooreAtkinson2008.xml
disagg_matrix(0.1)-lon_0.0-lat_0.0-smltp_source_model_2-gsimltp_ChiouYoungs2008.xml
disagg_matrix(0.1)-lon_-3.0-lat_-3.0-smltp_source_model_1-gsimltp_BooreAtkinson2008_YoungsEtAl1997SSlab.xml
disagg_matrix(0.1)-lon_-3.0-lat_-3.0-smltp_source_model_1-gsimltp_ChiouYoungs2008_YoungsEtAl1997SSlab.xml'''.split()
