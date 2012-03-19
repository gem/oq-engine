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


import unittest

from django.db import transaction
from django.db.utils import DatabaseError

from openquake import shapes
from openquake.db import models

from tests.utils import helpers


class DmgDistDbTriggerTestCase(unittest.TestCase):
    """These tests are meant to exercise the insert/update triggers for
    ensuring record validity."""

    DMG_STATES = ['no_damage', 'slight', 'moderate', 'extensive', 'complete']

    @classmethod
    def setUpClass(cls):
        default_user = helpers.default_user()

        cls.job = models.OqJob(owner=default_user)
        cls.job.save()

        cls.ddpa_output = models.Output(
            owner=default_user, oq_job=cls.job,
            display_name='Test dmg dist per asset',
            output_type='dmg_dist_per_asset',
            db_backed=True)
        cls.ddpa_output.save()

        cls.ddpa = models.DmgDistPerAsset(
            output=cls.ddpa_output, dmg_states=cls.DMG_STATES)
        cls.ddpa.save()

        # We also need some sample exposure data records (to satisfy the dmg
        # dist per asset FK).
        test_input = models.Input(
            owner=default_user, input_type='exposure', path='fake', size=0)
        test_input.save()
        exp_model = models.ExposureModel(
            owner=default_user, input=test_input, name='test-exp-model',
            category='economic loss', stco_type='per_asset', stco_unit='CHF')
        exp_model.save()

        test_site = shapes.Site(3.14, 2.17)
        cls.exp_data = models.ExposureData(  # Asset
            exposure_model=exp_model, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=37,
            site=test_site.point.to_wkt(), stco=1234.56)
        cls.exp_data.save()

    def test_dmg_dist_per_asset_data_valid_dmg_state(self):
        # We just want to test that there are no errors saving to the db.
        for ds in self.DMG_STATES:
            dd = models.DmgDistPerAssetData(
                dmg_dist_per_asset=self.ddpa, exposure_data=self.exp_data,
                dmg_state=ds, mean=0.0, stddev=0.0)
            dd.save()

    def test_dmg_dist_per_asset_data_invalid_dmg_state(self):
        expected_error = (
            "Exception: Invalid dmg_state 'invalid state', must be one of "
            "['no_damage', 'slight', 'moderate', 'extensive', 'complete'] "
            "(dmg_dist_per_asset_data)"
        )

        dd = models.DmgDistPerAssetData(
            dmg_dist_per_asset=self.ddpa, exposure_data=self.exp_data,
            dmg_state='invalid state', mean=0.0, stddev=0.0)
        try:
            dd.save()
        except DatabaseError, de:
            self.assertEqual(expected_error, de.message.split('\n')[0])
        else:
            self.fail("DatabaseError not raised")
