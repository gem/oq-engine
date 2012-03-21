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


from django.db import transaction
from django.db.utils import DatabaseError
from django.test import TestCase as DjangoTestCase

from openquake import shapes
from openquake.db import models

from tests.utils import helpers


class DamageStateTriggersTestCase(DjangoTestCase):
    """These tests are meant to exercise the insert/update triggers for
    ensuring that `dmg_state` values for dmg_dist_*_data records are valid."""

    DMG_STATES = ['no_damage', 'slight', 'moderate', 'extensive', 'complete']

    EXP_ERROR_FMT_STR = (
        "Exception: Invalid dmg_state 'invalid state', must be one of "
        "['no_damage', 'slight', 'moderate', 'extensive', 'complete'] "
        "(%s)"
    )

    GRID_CELL_SITE = shapes.Site(3.11, 2.14)

    @classmethod
    def setUpClass(cls):
        default_user = helpers.default_user()

        cls.job = models.OqJob(owner=default_user)
        cls.job.save()

        # dmg dist per asset
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

        # dmg dist per taxonomy
        cls.ddpt_output = models.Output(
            owner=default_user, oq_job=cls.job,
            display_name='Test dmg dist per taxonomy',
            output_type='dmg_dist_per_taxonomy',
            db_backed=True)
        cls.ddpt_output.save()

        cls.ddpt = models.DmgDistPerTaxonomy(
            output=cls.ddpt_output, dmg_states=cls.DMG_STATES)
        cls.ddpt.save()

        # total dmg dist
        cls.ddt_output = models.Output(
            owner=default_user, oq_job=cls.job,
            display_name='Test dmg dist total',
            output_type='dmg_dist_total',
            db_backed=True)
        cls.ddt_output.save()

        cls.ddt = models.DmgDistTotal(
            output=cls.ddt_output, dmg_states=cls.DMG_STATES)
        cls.ddt.save()

    def _test_insert_update_invalid(self, mdl, table):
        # Helper function for running tests for invalid damage states.
        mdl.dmg_state = 'invalid state'
        try:
            mdl.save()
        except DatabaseError, de:
            self.assertEqual(
                self.EXP_ERROR_FMT_STR % table,
                de.message.split('\n')[0])
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ddpa_insert_valid_dmg_state(self):
        for ds in self.DMG_STATES:
            dd = models.DmgDistPerAssetData(
                dmg_dist_per_asset=self.ddpa, exposure_data=self.exp_data,
                dmg_state=ds, mean=0.0, stddev=0.0,
                location=self.GRID_CELL_SITE.point.to_wkt())
            dd.save()

    def test_ddpa_insert_invalid_dmg_state(self):
        dd = models.DmgDistPerAssetData(
            dmg_dist_per_asset=self.ddpa, exposure_data=self.exp_data,
            mean=0.0, stddev=0.0, location=self.GRID_CELL_SITE.point.to_wkt())

        self._test_insert_update_invalid(dd, 'dmg_dist_per_asset_data')

    def test_ddpa_update_valid_dmg_state(self):
        dd = models.DmgDistPerAssetData(
            dmg_dist_per_asset=self.ddpa, exposure_data=self.exp_data,
            dmg_state='slight', mean=0.0, stddev=0.0,
            location=self.GRID_CELL_SITE.point.to_wkt())
        dd.save()

        dd.dmg_state = 'moderate'
        dd.save()

    def test_ddpa_update_invalid_dmg_state(self):
        dd = models.DmgDistPerAssetData(
            dmg_dist_per_asset=self.ddpa, exposure_data=self.exp_data,
            dmg_state='slight', mean=0.0, stddev=0.0,
            location=self.GRID_CELL_SITE.point.to_wkt())
        dd.save()

        self._test_insert_update_invalid(dd, 'dmg_dist_per_asset_data')

    def test_ddpt_insert_valid_dmg_state(self):
        for ds in self.DMG_STATES:
            dd = models.DmgDistPerTaxonomyData(
                dmg_dist_per_taxonomy=self.ddpt,
                taxonomy=helpers.random_string(), dmg_state=ds, mean=0.0,
                stddev=0.0)
            dd.save()

    def test_ddpt_insert_invalid_dmg_state(self):
        dd = models.DmgDistPerTaxonomyData(
            dmg_dist_per_taxonomy=self.ddpt, taxonomy=helpers.random_string(),
            mean=0.0, stddev=0.0)

        self._test_insert_update_invalid(dd, 'dmg_dist_per_taxonomy_data')

    def test_ddpt_update_valid_dmg_state(self):
        dd = models.DmgDistPerTaxonomyData(
            dmg_dist_per_taxonomy=self.ddpt,
            taxonomy=helpers.random_string(), dmg_state='extensive', mean=0.0,
            stddev=0.0)
        dd.save()

        dd.dmg_state = 'complete'
        dd.save()

    def test_ddpt_update_invalid_dmg_state(self):
        dd = models.DmgDistPerTaxonomyData(
            dmg_dist_per_taxonomy=self.ddpt,
            taxonomy=helpers.random_string(), dmg_state='extensive', mean=0.0,
            stddev=0.0)
        dd.save()

        self._test_insert_update_invalid(dd, 'dmg_dist_per_taxonomy_data')

    def test_ddt_insert_valid_dmg_state(self):
        for ds in self.DMG_STATES:
            dd = models.DmgDistTotalData(
                dmg_dist_total=self.ddt, dmg_state=ds, mean=0.0, stddev=0.0)
            dd.save()

    def test_ddt_insert_invalid_dmg_state(self):
        dd = models.DmgDistTotalData(
            dmg_dist_total=self.ddt, mean=0.0, stddev=0.0)

        self._test_insert_update_invalid(dd, 'dmg_dist_total_data')

    def test_ddt_update_valid_dmg_state(self):
        dd = models.DmgDistTotalData(
            dmg_dist_total=self.ddt, dmg_state='complete', mean=0.0,
            stddev=0.0)
        dd.save()

        dd.dmg_state = 'moderate'
        dd.save()

    def test_ddt_update_invalid_dmg_state(self):
        dd = models.DmgDistTotalData(
            dmg_dist_total=self.ddt, dmg_state='complete', mean=0.0,
            stddev=0.0)
        dd.save()

        self._test_insert_update_invalid(dd, 'dmg_dist_total_data')
