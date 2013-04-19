# Copyright (c) 2010-2013, GEM Foundation.
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

from shapely.geometry import Point
from openquake.engine.db import models
from openquake.engine import engine

from tests.utils import helpers


class DamageStateTestCase(DjangoTestCase):
    """These tests are meant to exercise the foreign keys
    ensuring that the `dmg_state` values are valid."""

    DMG_STATES = ['no_damage', 'slight', 'moderate', 'extensive', 'complete']

    GRID_CELL_SITE = Point(3.11, 2.14)

    @classmethod
    def setUpClass(cls):
        default_user = helpers.default_user()

        cls.job = models.OqJob(owner=default_user)
        rc = engine.create_risk_calculation(
            cls.job.owner,
            dict(calculation_mode='scenario_damage', base_path='/'), [])
        cls.job.risk_calculation = rc
        cls.job.save()

        # We also need some sample exposure data records (to satisfy the dmg
        # dist per asset FK).
        test_input = models.Input(
            owner=default_user, input_type='exposure', path='fake', size=0)
        test_input.save()
        i2j = models.Input2job(input=test_input, oq_job=cls.job)
        i2j.save()
        exp_model = models.ExposureModel(
            owner=default_user, input=test_input, name='test-exp-model',
            category='economic loss', stco_type='per_asset', stco_unit='CHF')
        exp_model.save()

        test_site = Point(3.14, 2.17)
        cls.exp_data = models.ExposureData(
            # Asset
            exposure_model=exp_model, asset_ref=helpers.random_string(),
            taxonomy=helpers.random_string(), number_of_units=37,
            site=test_site.to_wkt(), stco=1234.56)
        cls.exp_data.save()

        cls.dmg_states = {}

        for lsi, dmg_state in enumerate(cls.DMG_STATES):
            dstate = models.DmgState(
                risk_calculation=cls.job.risk_calculation,
                dmg_state=dmg_state, lsi=lsi)
            cls.dmg_states[dmg_state] = dstate
            dstate.save()
        cls.invalid_state = models.DmgState(
            risk_calculation=cls.job.risk_calculation,
            dmg_state='invalid state', lsi=0)

    def _test_insert_update_invalid(self, mdl, table):
        # Helper function for running tests for invalid damage states.
        mdl.dmg_state = self.invalid_state
        try:
            mdl.save()
        except DatabaseError:
            transaction.rollback()
        else:
            self.fail("DatabaseError not raised")

    def test_ddpa_insert_valid_dmg_state(self):
        for ds in self.dmg_states.itervalues():
            dd = models.DmgDistPerAsset(
                exposure_data=self.exp_data,
                dmg_state=ds, mean=0.0, stddev=0.0)
            dd.save()

    def test_ddpa_insert_invalid_dmg_state(self):
        dd = models.DmgDistPerAsset(
            exposure_data=self.exp_data, mean=0.0, stddev=0.0)
        self._test_insert_update_invalid(dd, 'dmg_dist_per_asset')

    def test_ddpa_update_valid_dmg_state(self):
        dd = models.DmgDistPerAsset(
            exposure_data=self.exp_data,
            dmg_state=self.dmg_states['slight'], mean=0.0, stddev=0.0)
        dd.save()
        dd.dmg_state = self.dmg_states['moderate']
        dd.save()

    def test_ddpa_update_invalid_dmg_state(self):
        dd = models.DmgDistPerAsset(
            exposure_data=self.exp_data,
            dmg_state=self.dmg_states['slight'], mean=0.0, stddev=0.0)
        dd.save()
        self._test_insert_update_invalid(dd, 'dmg_dist_per_asset')

    def test_ddpt_insert_valid_dmg_state(self):
        for ds in self.dmg_states.itervalues():
            dd = models.DmgDistPerTaxonomy(
                taxonomy=helpers.random_string(),
                dmg_state=ds, mean=0.0,
                stddev=0.0)
            dd.save()

    def test_ddpt_insert_invalid_dmg_state(self):
        dd = models.DmgDistPerTaxonomy(
            taxonomy=helpers.random_string(),
            mean=0.0, stddev=0.0)
        self._test_insert_update_invalid(dd, 'dmg_dist_per_taxonomy')

    def test_ddpt_update_valid_dmg_state(self):
        dd = models.DmgDistPerTaxonomy(
            taxonomy=helpers.random_string(),
            dmg_state=self.dmg_states['extensive'], mean=0.0,
            stddev=0.0)
        dd.save()
        dd.dmg_state = self.dmg_states['complete']
        dd.save()

    def test_ddpt_update_invalid_dmg_state(self):
        dd = models.DmgDistPerTaxonomy(
            taxonomy=helpers.random_string(),
            dmg_state=self.dmg_states['extensive'], mean=0.0,
            stddev=0.0)
        dd.save()
        self._test_insert_update_invalid(dd, 'dmg_dist_per_taxonomy')

    def test_ddt_insert_valid_dmg_state(self):
        for ds in self.dmg_states.itervalues():
            dd = models.DmgDistTotal(
                dmg_state=ds, mean=0.0, stddev=0.0)
            dd.save()

    def test_ddt_insert_invalid_dmg_state(self):
        dd = models.DmgDistTotal(mean=0.0, stddev=0.0)
        self._test_insert_update_invalid(dd, 'dmg_dist_total')

    def test_ddt_update_valid_dmg_state(self):
        dd = models.DmgDistTotal(
            dmg_state=self.dmg_states['complete'], mean=0.0,
            stddev=0.0)
        dd.save()
        dd.dmg_state = self.dmg_states['moderate']
        dd.save()

    def test_ddt_update_invalid_dmg_state(self):
        dd = models.DmgDistTotal(
            dmg_state=self.dmg_states['complete'], mean=0.0,
            stddev=0.0)
        dd.save()
        self._test_insert_update_invalid(dd, 'dmg_dist_total')
