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

import os
import unittest
import json

from django.contrib.gis import geos

from openquake.calculators.risk.classical.core import ClassicalRiskCalculator
from openquake.calculators.risk.general import BaseRiskCalculator
from openquake.calculators.risk.general import load_gmvs_at
from openquake.calculators.risk.general import hazard_input_site
from openquake.job import config
from openquake.db import models
from openquake import engine
from openquake import kvs
from openquake import shapes
from openquake.output.risk import LossMapDBWriter
from openquake.output.risk import LossMapNonScenarioXMLWriter

from tests.utils import helpers


class ProbabilisticRiskCalculatorTestCase(unittest.TestCase):
    """Tests for
    :class:`openquake.calculators.risk.general.ProbabilisticRiskCalculator`.
    """

    def test_write_output(self):
        # Test that the loss map writers are properly called when
        # write_output is invoked.
        cfg_file = helpers.demo_file('classical_psha_based_risk/config.gem')

        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(
            cfg_file, job)

        # Set conditional loss poe so that loss maps are created.
        # If this parameter is not specified, no loss maps will be serialized
        # at the end of the job.
        params['CONDITIONAL_LOSS_POE'] = '0.01'
        job_profile.conditional_loss_poe = [0.01]
        job_profile.save()

        job_ctxt = engine.JobContext(
            params, job.id, sections=sections,
            serialize_results_to=['xml', 'db'], oq_job_profile=job_profile,
            oq_job=job)

        calculator = ClassicalRiskCalculator(job_ctxt)

        # Mock the composed loss map serializer:
        with helpers.patch('openquake.writer.CompositeWriter'
                           '.serialize') as writer_mock:
            calculator.write_output()

            self.assertEqual(1, writer_mock.call_count)

            # Now test that the composite writer got the correct
            # 'serialize to' instructions. The composite writer should have
            # 1 DB and 1 XML loss map serializer:
            composite_writer = writer_mock.call_args[0][0]
            writers = composite_writer.writers

            self.assertEqual(2, len(writers))
            # We don't assume anything about the order of the writers,
            # and we don't care anyway in this test:
            self.assertTrue(any(
                isinstance(w, LossMapDBWriter) for w in writers))
            self.assertTrue(any(
                isinstance(w, LossMapNonScenarioXMLWriter) for w in writers))


class BaseRiskCalculatorTestCase(unittest.TestCase):
    """Tests for
    :class:`openquake.calculators.risk.general.BaseRiskCalculator`.
    """

    def test__serialize_xml_filenames(self):
        # Test that the file names of the loss XML artifacts are correct.
        # See https://bugs.launchpad.net/openquake/+bug/894706.
        expected_lrc_file_name = (
            'losscurves-block-#%(job_id)s-block#%(block)s.xml')
        expected_lr_file_name = (
            'losscurves-loss-block-#%(job_id)s-block#%(block)s.xml')

        cfg_file = helpers.demo_file('classical_psha_based_risk/config.gem')

        job = engine.prepare_job()
        job_profile, params, sections = engine.import_job_profile(
            cfg_file, job)

        job_ctxt = engine.JobContext(
            params, job.id, sections=sections,
            serialize_results_to=['xml', 'db'], oq_job_profile=job_profile,
            oq_job=job)

        calculator = ClassicalRiskCalculator(job_ctxt)

        with helpers.patch('openquake.writer.FileWriter.serialize'):
            # The 'curves' key in the kwargs just needs to be present;
            # because of the serialize mock in place above, it doesn't need
            # to have a real value.

            # First, we test loss ratio curve output,
            # then we'll do the same test for loss curve output.

            # We expect to get a single file path back.
            [file_path] = calculator._serialize(
                0, **dict(curve_mode='loss_ratio', curves=[]))

            _dir, file_name = os.path.split(file_path)

            self.assertEqual(
                expected_lrc_file_name % dict(job_id=job.id,
                                              block=0),
                file_name)

            # The same test again, except for loss curves this time.
            [file_path] = calculator._serialize(
                0, **dict(curve_mode='loss', curves=[]))

            _dir, file_name = os.path.split(file_path)

            self.assertEqual(
                expected_lr_file_name % dict(job_id=job.id,
                                             block=0),
                file_name)

RISK_DEMO_CONFIG_FILE = helpers.demo_file(
    "classical_psha_based_risk/config.gem")


class AssetsForCellTestCase(unittest.TestCase, helpers.DbTestCase):
    """Test the BaseRiskCalculator.assets_for_cell() function."""

    job = None
    sites = []
    job_ctxt = None

    @classmethod
    def setUpClass(cls):
        cls.job = engine.prepare_job()
        jp, _, _ = engine.import_job_profile(RISK_DEMO_CONFIG_FILE, cls.job)

        cls.job_ctxt = helpers.create_job({}, job_id=cls.job.id,
                                          oq_job_profile=jp, oq_job=cls.job)
        calc = ClassicalRiskCalculator(cls.job_ctxt)

        calc.store_exposure_assets()
        [input] = models.inputs4job(cls.job.id, input_type="exposure")
        model = input.model()
        assets = model.exposuredata_set.filter(taxonomy="af/ctc-D/LR")
        # Add some more assets.
        coos = [(10.000155392289116, 46.546194318563),
                (10.222034128255, 46.0071299176413),
                (10.520376165581, 46.247463385278)]
        for lat, lon in coos:
            site = shapes.Site(lat, lon)
            cls.sites.append(site)
            if assets:
                continue
            location = geos.GEOSGeometry(site.point.to_wkt())
            asset = models.ExposureData(
                exposure_model=model, taxonomy="af/ctc-D/LR",
                asset_ref=helpers.random_string(6), stco=lat * 2,
                site=location, reco=1.1 * lon)
            asset.save()

    @staticmethod
    def _to_site(pg_point):
        return shapes.Site(pg_point.x, pg_point.y)

    def test_assets_for_cell_with_more_than_one(self):
        # All assets in the risk cell are found.
        site = shapes.Site(10.3, 46.3)
        self.job_ctxt.oq_job_profile.region_grid_spacing = 0.6
        self.job_ctxt.oq_job_profile.save()

        assets = BaseRiskCalculator.assets_for_cell(self.job.id, site)
        self.assertEqual(3, len(assets))
        # Make sure the assets associated with the first 3 added sites were
        # selected.
        for s, a in zip(self.sites, sorted(assets, key=lambda a: a.site.x)):
            self.assertEqual(s, self._to_site(a.site))

    def test_assets_for_cell_with_one(self):
        # A single asset in the risk cell is found.
        site = shapes.Site(10.15, 46.15)
        self.job_ctxt.oq_job_profile.region_grid_spacing = 0.3
        self.job_ctxt.oq_job_profile.save()
        [asset] = BaseRiskCalculator.assets_for_cell(self.job.id, site)
        self.assertEqual(self.sites[1], self._to_site(asset.site))

    def test_assets_for_cell_with_no_assets_matching(self):
        # An empty list is returned when no assets exist for a given
        # risk cell.
        site = shapes.Site(99.15000, 15.16667)
        self.job_ctxt.oq_job_profile.region_grid_spacing = 0.05
        self.job_ctxt.oq_job_profile.save()
        self.assertEqual([],
                         BaseRiskCalculator.assets_for_cell(self.job.id, site))


class AssetsAtTestCase(unittest.TestCase, helpers.DbTestCase):

    @classmethod
    def setUpClass(cls):
        cls.job = engine.prepare_job()
        jp, _, _ = engine.import_job_profile(RISK_DEMO_CONFIG_FILE, cls.job)
        calc_proxy = helpers.create_job({}, job_id=cls.job.id,
                oq_job_profile=jp, oq_job=cls.job)

        # storing the basic exposure model
        ClassicalRiskCalculator(calc_proxy).store_exposure_assets()
        [input] = models.inputs4job(cls.job.id, input_type="exposure")
        model = input.model()
        assets = model.exposuredata_set.filter(taxonomy="aa/aatc-D/LR")

        if not assets:
            # This model did not exist in the database before.
            site = shapes.Site(1.0, 2.0)
            # more assets at same location
            models.ExposureData(
                exposure_model=model, taxonomy="aa/aatc-D/LR",
                asset_ref="ASSET_1", stco=1,
                site=geos.GEOSGeometry(site.point.to_wkt()), reco=1).save()

            models.ExposureData(
                exposure_model=model, taxonomy="aa/aatc-D/LR",
                asset_ref="ASSET_2", stco=1,
                site=geos.GEOSGeometry(site.point.to_wkt()), reco=1).save()

            site = shapes.Site(2.0, 2.0)
            # just one asset at location
            models.ExposureData(
                exposure_model=model, taxonomy="aa/aatc-D/LR",
                asset_ref="ASSET_3", stco=1,
                site=geos.GEOSGeometry(site.point.to_wkt()), reco=1).save()

    def test_one_asset_per_site(self):
        site = shapes.Site(2.0, 2.0)
        assets = BaseRiskCalculator.assets_at(self.job.id, site)

        self.assertEqual(1, len(assets))
        self.assertEqual("ASSET_3", assets[0].asset_ref)

    def test_multiple_assets_per_site(self):
        site = shapes.Site(1.0, 2.0)
        assets = BaseRiskCalculator.assets_at(self.job.id, site)

        self.assertEqual(2, len(assets))
        self.assertEqual("ASSET_1", assets[0].asset_ref)
        self.assertEqual("ASSET_2", assets[1].asset_ref)

    def test_no_assets_at_site(self):
        # nothing is stored at this location
        site = shapes.Site(10.0, 10.0)

        self.assertEqual([], BaseRiskCalculator.assets_at(self.job.id, site))


class LoadGroundMotionValuesTestCase(unittest.TestCase):

    job_id = "1234"
    region = shapes.Region.from_simple((0.1, 0.1), (0.2, 0.2))

    def setUp(self):
        kvs.mark_job_as_current(self.job_id)
        kvs.cache_gc(self.job_id)

    def tearDown(self):
        kvs.mark_job_as_current(self.job_id)
        kvs.cache_gc(self.job_id)

    def test_load_gmvs_at(self):
        """
        Exercise the function
        :func:`openquake.calculators.risk.general.load_gmvs_at`.
        """

        gmvs = [
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.117},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.167},
            {'site_lon': 0.1, 'site_lat': 0.2, 'mag': 0.542}]

        expected_gmvs = [0.117, 0.167, 0.542]
        point = self.region.grid.point_at(shapes.Site(0.1, 0.2))

        # we expect this point to be at row 1, column 0
        self.assertEqual(1, point.row)
        self.assertEqual(0, point.column)

        key = kvs.tokens.ground_motion_values_key(self.job_id, point)

        # place the test values in kvs
        for gmv in gmvs:
            kvs.get_client().rpush(key, json.JSONEncoder().encode(gmv))

        actual_gmvs = load_gmvs_at(self.job_id, point)
        self.assertEqual(expected_gmvs, actual_gmvs)


class HazardInputSiteTestCase(unittest.TestCase):

    def test_hazard_input_is_the_exposure_site(self):
        # when `COMPUTE_HAZARD_AT_ASSETS_LOCATIONS` is specified,
        # the hazard must be looked up on the same risk location
        # (the input parameter of the function)
        params = {config.COMPUTE_HAZARD_AT_ASSETS: True}
        job_ctxt = engine.JobContext(params, None)

        self.assertEqual(shapes.Site(1.0, 1.0), hazard_input_site(
                job_ctxt, shapes.Site(1.0, 1.0)))

    def test_hazard_input_is_the_cell_center(self):
        # when `COMPUTE_HAZARD_AT_ASSETS_LOCATIONS` is not specified,
        # the hazard must be looked up on the center of the cell
        # where the given site falls in
        params = {config.INPUT_REGION: \
            "1.0, 1.0, 2.0, 1.0, 2.0, 2.0, 1.0, 2.0",
            config.REGION_GRID_SPACING: 0.5}

        job_ctxt = engine.JobContext(params, None)

        self.assertEqual(shapes.Site(1.0, 1.0), hazard_input_site(
                job_ctxt, shapes.Site(1.2, 1.2)))

        self.assertEqual(shapes.Site(1.5, 1.5), hazard_input_site(
                job_ctxt, shapes.Site(1.6, 1.6)))
