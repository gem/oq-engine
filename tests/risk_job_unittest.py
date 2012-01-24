# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

import mock
import os
import redis
import unittest

from openquake import kvs
from openquake import shapes
from openquake.job import config
from openquake.parser import exposure
from openquake.calculators.risk import general

from tests.utils import helpers

TEST_FILE = "exposure-portfolio.xml"
EXPOSURE_TEST_FILE = "exposure-portfolio.xml"


class EpsilonTestCase(unittest.TestCase):
    """Tests the `epsilon` method in class `EpsilonProvider`"""

    def setUp(self):
        self.exposure_parser = exposure.ExposurePortfolioFile(
            os.path.join(helpers.SCHEMA_EXAMPLES_DIR, TEST_FILE))
        self.epsilon_provider = general.EpsilonProvider(dict())

    def test_uncorrelated(self):
        """For uncorrelated jobs we sample epsilon values per asset.

        A new sample should be drawn for each asset irrespective of any
        building typology similarities.
        """
        samples = []
        for _, asset in self.exposure_parser:
            sample = self.epsilon_provider.epsilon(asset)
            self.assertTrue(sample not in samples,
                            "%s is already in %s" % (sample, samples))
            self.assertTrue(isinstance(sample, float),
                            "Invalid sample (%s)" % sample)
            samples.append(sample)

    def test_correlated(self):
        """For correlated jobs we sample epsilon values per building typology.

        A sample should be drawn whenever an asset with a new building typology
        is encountered. Assets of the same typology should share sample values.
        Please not that building typologies and taxonomies are roughly
        equivalent.
        """
        samples = dict()
        self.epsilon_provider.__dict__["ASSET_CORRELATION"] = "perfect"
        for _, asset in self.exposure_parser:
            sample = self.epsilon_provider.epsilon(asset)
            taxonomy = asset["taxonomy"]
            # This is either the first time we see this taxonomy or the sample
            # is identical to the one originally drawn for this taxonomy.
            if taxonomy not in samples:
                samples[taxonomy] = sample
            else:
                self.assertTrue(sample == samples[taxonomy])
        # Make sure we used at least two taxonomies in this test.
        self.assertTrue(len(samples.keys()) > 1)
        # Are all samples valid values?
        for taxonomy, sample in samples.iteritems():
            self.assertTrue(
                isinstance(sample, float),
                "Invalid sample (%s) for taxonomy %s" % (sample, taxonomy))

    def test_incorrect_configuration_setting(self):
        """The correctness of the asset correlation configuration is enforced.

        If the `ASSET_CORRELATION` parameter is set in the job configuration
        file it should have a correct value ("perfect").
        """
        self.epsilon_provider.__dict__["ASSET_CORRELATION"] = "this-is-wrong"
        for _, asset in self.exposure_parser:
            self.assertRaises(ValueError, self.epsilon_provider.epsilon, asset)
            break

    def test_correlated_with_no_taxonomy(self):
        """For correlated jobs assets require a taxonomy property."""
        self.epsilon_provider.__dict__["ASSET_CORRELATION"] = "perfect"
        for _, asset in self.exposure_parser:
            del asset["taxonomy"]
            self.assertRaises(ValueError, self.epsilon_provider.epsilon, asset)
            break


class BlockTestCase(unittest.TestCase):

    def setUp(self):
        self.site = shapes.Site(1.0, 1.0)

    def test_can_serialize_a_block_into_kvs(self):
        block = general.Block((self.site, self.site), 'test_block_id')
        block.to_kvs()

        self.assertEqual(block, general.Block.from_kvs(block.id))


class BlockSplitterTestCase(unittest.TestCase):

    def setUp(self):
        self.site_1 = shapes.Site(1.0, 1.0)
        self.site_2 = shapes.Site(2.0, 1.0)
        self.site_3 = shapes.Site(3.0, 1.0)

    def test_an_empty_set_produces_no_blocks(self):
        self._assert_number_of_blocks_is((), expected=0, block_size=1)

    def test_splits_the_set_into_a_single_block(self):
        self._assert_number_of_blocks_is(
            (self.site_1, ), expected=1, block_size=3)

        self._assert_number_of_blocks_is(
            (self.site_1, self.site_1), expected=1, block_size=3)

        self._assert_number_of_blocks_is(
            (self.site_1, self.site_1, self.site_1), expected=1, block_size=3)

    def test_splits_the_set_into_multiple_blocks(self):
        self._assert_number_of_blocks_is(
            (self.site_1, self.site_1), expected=2, block_size=1)

        self._assert_number_of_blocks_is(
            (self.site_1, self.site_1, self.site_1), expected=2, block_size=2)

    def test_generates_the_correct_blocks(self):
        expected = (
            general.Block((self.site_1, self.site_2, self.site_3), None), )

        self._assert_blocks_are(
            expected, (self.site_1, self.site_2, self.site_3), block_size=3)

        expected = (
            general.Block((self.site_1, self.site_2), None),
            general.Block((self.site_3, ), None))

        self._assert_blocks_are(
            expected, (self.site_1, self.site_2, self.site_3), block_size=2)

    def _check_block_key(self, job_id, block):
        self.assertTrue(kvs.tokens.generate_job_key(job_id) in block.id,
                        "Job id %s contained in key %s" % (
                job_id, block.id))

    def _assert_blocks_are(self, expected, sites, block_size):
        for idx, block in enumerate(
            general.split_into_blocks(123, sites, block_size)):

            self._check_block_key(123, block)
            self.assertEqual(expected[idx], block)

    def _assert_number_of_blocks_is(self, sites, expected, block_size):
        counter = 0

        for block in general.split_into_blocks(123, sites, block_size):
            counter += 1
            self._check_block_key(123, block)

        self.assertEqual(expected, counter)


class BaseRiskCalculatorTestCase(unittest.TestCase):

    def test_prepares_blocks_using_the_exposure(self):
        """The base risk calculator is able to read the exposure file,
        split the sites into blocks and store them in KVS.
        """

        params = {
            config.EXPOSURE: os.path.join(helpers.SCHEMA_EXAMPLES_DIR,
                                          EXPOSURE_TEST_FILE),
            "BASE_PATH": "."
        }
        a_job = helpers.create_job(params)

        calculator = general.BaseRiskCalculator(a_job)

        calculator.partition()

        expected = general.Block(
            (shapes.Site(9.15000, 45.16667), shapes.Site(9.15333, 45.12200),
             shapes.Site(9.14777, 45.17999)), None)

        self.assertEqual(1, len(a_job.blocks_keys))

        self.assertEqual(
            expected, general.Block.from_kvs(a_job.blocks_keys[0]))

    def test_prepares_blocks_using_the_exposure_and_filtering(self):
        """When reading the exposure file, the calculator also provides
        filtering on the region specified in the REGION_VERTEX and
        REGION_GRID_SPACING paramaters.
        """

        region_vertex = \
            "46.0, 9.14, 46.0, 9.15, 45.0, 9.15, 45.0, 9.14"

        params = {config.EXPOSURE: os.path.join(
                helpers.SCHEMA_EXAMPLES_DIR, EXPOSURE_TEST_FILE),
                config.INPUT_REGION: region_vertex,
                config.REGION_GRID_SPACING: 0.1,
                config.CALCULATION_MODE: "Event Based"}

        a_job = helpers.create_job(params)

        expected_block = general.Block(
            (shapes.Site(9.15, 45.16667), shapes.Site(9.14777, 45.17999)),
            None)

        calculator = general.BaseRiskCalculator(a_job)

        calculator.partition()

        self.assertEqual(1, len(a_job.blocks_keys))

        self.assertEqual(
            expected_block, general.Block.from_kvs(a_job.blocks_keys[0]))


GRID_ASSETS = {
    (0, 0): {'assetID': 'asset_at_0_0', 'lat': 10.0, 'lon': 10.0},
    (0, 1): {'assetID': 'asset_at_0_1', 'lat': 10.0, 'lon': 10.1},
    (1, 0): {'assetID': 'asset_at_1_0', 'lat': 10.1, 'lon': 10.0},
    (1, 1): {'assetID': 'asset_at_1_1', 'lat': 10.1, 'lon': 10.1}}


class RiskCalculatorTestCase(unittest.TestCase):

    def setUp(self):
        self.job = helpers.job_from_file(os.path.join(helpers.DATA_DIR,
                                         'config.gem'))

        self.grid = shapes.Grid(shapes.Region.from_coordinates(
            [(1.0, 3.0), (1.0, 4.0), (2.0, 4.0), (2.0, 3.0)]),
            1.0)

        # this is the expected output of grid_assets_iterator and an input of
        # asset_losses_per_site
        self.grid_assets = [
            (shapes.GridPoint(self.grid, 0, 0), GRID_ASSETS[(0, 0)]),
            (shapes.GridPoint(self.grid, 1, 0), GRID_ASSETS[(0, 1)]),
            (shapes.GridPoint(self.grid, 0, 1), GRID_ASSETS[(1, 0)]),
            (shapes.GridPoint(self.grid, 1, 1), GRID_ASSETS[(1, 1)])]

    def test_grid_assets_iterator(self):
        with helpers.patch('openquake.kvs.get_list_json_decoded') as get_mock:

            def get_list_json_decoded(key):
                row, col = kvs.tokens.asset_row_col_from_kvs_key(key)

                return [GRID_ASSETS[(row, col)]]

            get_mock.side_effect = get_list_json_decoded

            def row_col(item):
                return item[0].row, item[0].column

            calculator = general.BaseRiskCalculator(self.job)

            got = sorted(calculator.grid_assets_iterator(self.grid),
                         key=row_col)

            self.assertEqual(sorted(self.grid_assets, key=row_col), got)

    def test_that_conditional_loss_is_in_kvs(self):
        asset = {"assetID": 1}
        loss_poe = 0.1
        job_id = "1"
        col = 1
        row = 2
        loss_curve = shapes.Curve([(0.21, 0.131), (0.24, 0.108),
                (0.27, 0.089), (0.30, 0.066)])

        # should set in kvs the conditional loss
        general.compute_conditional_loss(job_id, col, row, loss_curve, asset,
                loss_poe)
        loss_key = kvs.tokens.loss_key(job_id, row, col,
                asset["assetID"], loss_poe)

        self.assertTrue(kvs.get_client().get(loss_key))

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

            calculator = general.BaseRiskCalculator(self.job)

            self.assertEqual(
                sorted(expected, key=coords),
                sorted(
                    calculator.asset_losses_per_site(
                        0.5, self.grid_assets),
                    key=coords))
