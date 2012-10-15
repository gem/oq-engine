# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import mock
import os
import redis
import unittest

from django.contrib.gis import geos

from openquake import engine
from openquake import kvs
from openquake import shapes
from openquake.calculators.risk import general
from openquake.calculators.risk.general import Block
from openquake.db import models
from openquake.input.exposure import ExposureDBWriter
from openquake.parser import exposure
from risklib import curve

import risklib
from tests.utils import helpers

TEST_FILE = "exposure-portfolio.xml"
EXPOSURE_TEST_FILE = "exposure-portfolio.xml"


class BlockTestCase(unittest.TestCase):
    """Tests for the :class:`openquake.calculators.risk.general.Block` class.
    """

    def test_eq(self):
        # Test the __eq__ method.
        # __eq__ is a shallow test and only compares ids.
        block1 = Block(7, 0, [shapes.Site(1.0, 1.0)])
        block2 = Block(7, 0, [shapes.Site(1.0, 0.0)])

        self.assertTrue(block1 == block2)

    def test_not_eq(self):
        # Test __eq__ with 2 Blocks that should not be equal
        block1 = Block(7, 0, [shapes.Site(1.0, 1.0)])
        block2 = Block(8, 0, [shapes.Site(1.0, 1.0)])
        self.assertFalse(block1 == block2)

        block1 = Block(7, 0, [shapes.Site(1.0, 1.0)])
        block2 = Block(7, 1, [shapes.Site(1.0, 1.0)])
        self.assertFalse(block1 == block2)

    def test_block_kvs_serialization(self):
        # Test that a Block is properly serialized/deserialized from the cache.
        job_id = 7
        block_id = 0
        expected_block = Block(job_id, block_id,
                               [shapes.Site(1.0, 1.0), shapes.Site(2.0, 2.0)])
        expected_block.to_kvs()

        actual_block = Block.from_kvs(job_id, block_id)

        self.assertEqual(expected_block, actual_block)
        # The sites are not compared in Block.__eq__; we need to check those
        # also.
        self.assertEqual(expected_block.sites, actual_block.sites)


class BlockSplitterTestCase(unittest.TestCase):

    def setUp(self):
        self.site_1 = shapes.Site(1.0, 1.0)
        self.site_2 = shapes.Site(2.0, 1.0)
        self.site_3 = shapes.Site(3.0, 1.0)
        self.site_4 = shapes.Site(4.0, 1.0)
        self.site_5 = shapes.Site(5.0, 1.0)
        self.site_6 = shapes.Site(6.0, 1.0)
        self.site_7 = shapes.Site(7.0, 1.0)
        self.site_8 = shapes.Site(8.0, 1.0)

        self.all_sites = [
            self.site_1,
            self.site_2,
            self.site_3,
            self.site_4,
            self.site_5,
            self.site_6,
            self.site_7,
            self.site_8
        ]

        self.job_id = 7

    def test_split_into_blocks(self):
        # Test a typical split case.
        # We will use a block size of 3, which will
        # give us 2 blocks of 3 sites and 1 block of 2 sites.
        expected = [
            Block(self.job_id, 0, self.all_sites[:3]),
            Block(self.job_id, 1, self.all_sites[3:6]),
            Block(self.job_id, 2, self.all_sites[6:])
        ]

        actual = [block for block in general.split_into_blocks(
            self.job_id, self.all_sites, block_size=3)]

        self.assertEqual(expected, actual)

    def test_split_block_size_eq_1(self):
        # Test splitting when block_size==1.
        expected = [Block(self.job_id, i, [self.all_sites[i]])
            for i in xrange(len(self.all_sites))]

        actual = [block for block in general.split_into_blocks(
            self.job_id, self.all_sites, block_size=1)]

        self.assertEqual(expected, actual)

    def test_split_empty_site_list(self):
        # If `split_into_blocks` is given an empty site list, the generator
        # shouldn't yield anything.
        actual = [block for block in general.split_into_blocks(
            self.job_id, [])]

        self.assertEqual([], actual)

    def test_split_block_size_eq_to_site_list_size(self):
        # If the block size is equal to the input site list size,
        # the generator should just yield a single block containing all of the
        # sites.
        actual = [block for block in general.split_into_blocks(
            self.job_id, self.all_sites, block_size=8)]

        self.assertEqual(
            [Block(self.job_id, 0, self.all_sites)],
            actual)

    def test_split_block_size_gt_site_list_size(self):
        # If the block size is greater than the input site list size,
        # the generator should just yield a single block containing all of the
        # sites.
        actual = [block for block in general.split_into_blocks(
            self.job_id, self.all_sites, block_size=9)]

        self.assertEqual(
            [Block(self.job_id, 0, self.all_sites)],
            actual)

    def test_split_block_size_lt_1(self):
        # If the specified block_size is less than 1, this is invalid.
        # We expect a RuntimeError to be raised.
        gen = general.split_into_blocks(self.job_id, self.all_sites,
                                        block_size=0)
        self.assertRaises(RuntimeError, gen.next)

        gen = general.split_into_blocks(self.job_id, self.all_sites,
                                        block_size=-1)
        self.assertRaises(RuntimeError, gen.next)


class BaseRiskCalculatorTestCase(unittest.TestCase):

    def setUp(self):
        self.job = engine.prepare_job()

    def test_partition(self):
        job_cfg = helpers.demo_file('classical_psha_based_risk/config.gem')
        job_profile, params, sections = engine.import_job_profile(
            job_cfg, self.job, force_inputs=True)
        job_ctxt = engine.JobContext(
            params, self.job.id, sections=sections, oq_job_profile=job_profile)

        calc = general.BaseRiskCalculator(job_ctxt)
        calc.store_exposure_assets()

        calc.partition()

        expected_blocks_keys = [0]
        self.assertEqual(expected_blocks_keys, job_ctxt.blocks_keys)

        expected_sites = [shapes.Site(-122.0, 38.225)]
        expected_block = general.Block(self.job.id, 0, expected_sites)

        actual_block = general.Block.from_kvs(self.job.id, 0)
        self.assertEqual(expected_block, actual_block)
        self.assertEqual(expected_block.sites, actual_block.sites)


GRID_ASSETS = {
    (0, 0): None,
    (0, 1): None,
    (1, 0): None,
    (1, 1): None}


class RiskCalculatorTestCase(unittest.TestCase):

    def setUp(self):
        self.job_ctxt = helpers.job_from_file(os.path.join(helpers.DATA_DIR,
                                              'config.gem'))
        [input] = models.inputs4job(self.job_ctxt.job_id,
                                    input_type="exposure")
        owner = models.OqUser.objects.get(user_name="openquake")
        emdl = input.model()
        if not emdl:
            emdl = models.ExposureModel(
                owner=owner, input=input, description="RCT exposure model",
                category="RCT villas", stco_unit="roofs",
                stco_type="aggregated")
            emdl.save()

        asset_data = [
            ((0, 0), shapes.Site(10.0, 10.0),
             {u'stco': 5.07, u'asset_ref': u'a5625',
              u'taxonomy': u'rctc-ad-83'}),

            ((0, 1), shapes.Site(10.1, 10.0),
             {u'stco': 5.63, u'asset_ref': u'a5629',
              u'taxonomy': u'rctc-ad-83'}),

            ((1, 0), shapes.Site(10.0, 10.1),
             {u'stco': 11.26, u'asset_ref': u'a5630',
              u'taxonomy': u'rctc-ad-83'}),

            ((1, 1), shapes.Site(10.1, 10.1),
             {u'stco': 5.5, u'asset_ref': u'a5636',
              u'taxonomy': u'rctc-ad-83'}),
        ]
        assets = emdl.exposuredata_set.filter(taxonomy="rctc-ad-83"). \
                                       order_by("id")
        for idx, (gcoo, site, adata) in enumerate(asset_data):
            if not assets:
                location = geos.GEOSGeometry(site.point.to_wkt())
                asset = models.ExposureData(exposure_model=emdl, site=location,
                                            **adata)
                asset.save()
            else:
                asset = assets[idx]
            GRID_ASSETS[gcoo] = asset

        self.grid = shapes.Grid(shapes.Region.from_coordinates(
            [(10.0, 10.0), (10.0, 10.1), (10.1, 10.1), (10.1, 10.0)]), 0.1)

        # this is the expected output of grid_assets_iterator and an input of
        # asset_losses_per_site
        self.grid_assets = [
            (shapes.GridPoint(self.grid, 0, 0), GRID_ASSETS[(0, 0)]),
            (shapes.GridPoint(self.grid, 1, 0), GRID_ASSETS[(0, 1)]),
            (shapes.GridPoint(self.grid, 0, 1), GRID_ASSETS[(1, 0)]),
            (shapes.GridPoint(self.grid, 1, 1), GRID_ASSETS[(1, 1)])]

    def test_grid_assets_iterator(self):
        def row_col(item):
            return item[0].row, item[0].column

        jp = models.profile4job(self.job_ctxt.job_id)
        jp.region_grid_spacing = 0.01
        jp.save()
        calculator = general.BaseRiskCalculator(self.job_ctxt)

        expected = sorted(self.grid_assets, key=row_col)
        actual = sorted(calculator.grid_assets_iterator(self.grid),
                        key=row_col)

        self.assertEqual(expected, actual)

    def test_asset_losses_per_site(self):
        mm = mock.MagicMock(spec=redis.Redis)
        mm.get.return_value = 0.123
        with helpers.patch('openquake.kvs.get_client') as mgc:
            mgc.return_value = mm

            def coords(item):
                return item[0].coords

            expected = [
                (shapes.Site(10.0, 10.0),
                    [({'value': 0.123}, GRID_ASSETS[(0, 0)])]),
                (shapes.Site(10.1, 10.0),
                    [({'value': 0.123}, GRID_ASSETS[(0, 1)])]),
                (shapes.Site(10.0, 10.1),
                    [({'value': 0.123}, GRID_ASSETS[(1, 0)])]),
                (shapes.Site(10.1, 10.1),
                    [({'value': 0.123}, GRID_ASSETS[(1, 1)])])]

            calculator = general.BaseRiskCalculator(self.job_ctxt)
            actual = calculator.asset_losses_per_site(0.5, self.grid_assets)
            expected = sorted(expected, key=coords)
            actual = sorted(actual, key=coords)

            self.assertEqual(expected, actual)
