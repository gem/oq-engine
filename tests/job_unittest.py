# -*- coding: utf-8 -*-

import math
import os
import unittest

from opengem import shapes
from opengem import test
from opengem import job
from opengem.job import Job, EXPOSURE, INPUT_REGION
from opengem.job.mixins import Mixin
from opengem.risk.job import RiskJobMixin
from opengem.risk.job.probabilistic import ProbabilisticEventMixin

CONFIG_FILE = "config.gem"
CONFIG_WITH_INCLUDES = "config_with_includes.gem"

TEST_JOB_FILE = test.smoketest_file('nshmp-california-fault/config.gem')

SITE = shapes.Site(1.0, 1.0)
EXPOSURE_TEST_FILE = "ExposurePortfolioFile-test.xml"
REGION_EXPOSURE_TEST_FILE = "ExposurePortfolioFile-test.region"
BLOCK_SPLIT_TEST_FILE = "block_split.gem"
REGION_TEST_FILE = "small.region"


class JobTestCase(unittest.TestCase):
    def setUp(self):
        self.job = Job.from_file(test.test_file(CONFIG_FILE))
        self.job_with_includes = Job.from_file(test.test_file(CONFIG_WITH_INCLUDES))

    def test_configuration_is_the_same_no_matter_which_way_its_provided(self):
        self.assertEqual(self.job.params, self.job_with_includes.params)

    def test_job_mixes_in_properly(self):
        with Mixin(self.job, RiskJobMixin, key="risk"):
            self.assertTrue(RiskJobMixin in self.job.__class__.__bases__)
            self.assertTrue(ProbabilisticEventMixin in self.job.__class__.__bases__)

        with Mixin(self.job, ProbabilisticEventMixin):
            self.assertTrue(ProbabilisticEventMixin in self.job.__class__.__bases__)

    def test_job_runs_with_a_good_config(self):
        job = Job.from_file(TEST_JOB_FILE)
        self.assertTrue(job.launch())

    def test_a_job_has_an_identifier(self):
        self.assertEqual(1, Job({}, 1).id)
    
    def test_can_store_and_read_jobs_from_kvs(self):
        self.job = Job.from_file(os.path.join(test.DATA_DIR, CONFIG_FILE))
        self.assertEqual(self.job, Job.from_kvs(self.job.id))

    def test_prepares_blocks_using_the_exposure(self):
        a_job = Job({EXPOSURE: os.path.join(test.DATA_DIR, EXPOSURE_TEST_FILE)})
        a_job._partition()
        blocks_keys = a_job.blocks_keys
        
        expected_block = job.Block((shapes.Site(9.15000, 45.16667),
                shapes.Site(9.15333, 45.12200), shapes.Site(9.14777, 45.17999),
                shapes.Site(9.15765, 45.13005), shapes.Site(9.15934, 45.13300),
                shapes.Site(9.15876, 45.13805)))
        
        self.assertEqual(1, len(blocks_keys))
        self.assertEqual(expected_block, job.Block.from_kvs(blocks_keys[0]))

    def test_prepares_blocks_using_the_exposure_and_filtering(self):
        a_job = Job({EXPOSURE: test.test_file(EXPOSURE_TEST_FILE), 
                     INPUT_REGION: test.test_file(REGION_EXPOSURE_TEST_FILE)})
        a_job._partition()
        blocks_keys = a_job.blocks_keys

        print blocks_keys
        print job.Block.from_kvs(blocks_keys[0]).sites
            
        expected_block = job.Block((shapes.Site(9.15, 45.16667),
                                    shapes.Site(9.15333, 45.122),
                                    shapes.Site(9.14777, 45.17999),
                                    shapes.Site(9.15765, 45.13005),
                                    shapes.Site(9.15934, 45.133),
                                    shapes.Site(9.15876, 45.13805)))

        self.assertEqual(1, len(blocks_keys))
        self.assertEqual(expected_block, job.Block.from_kvs(blocks_keys[0]))
    
    def test_prepares_blocks_using_the_input_region(self):
        """ This test might be currently catastrophically retarded. If it is
        blame Lars.
        """

        block_path = test.test_file(BLOCK_SPLIT_TEST_FILE)

        print "In open job"
        a_job = Job.from_file(block_path)

        verts = [float(x) for x in a_job.params['REGION_VERTEX'].split(",")]
        # Flips lon and lat, and builds a list of coord tuples
        coords = zip(verts[1::2], verts[::2])
        expected = shapes.RegionConstraint.from_coordinates(coords)
        expected.cell_size = float(a_job.params['REGION_GRID_SPACING'])

        expected_sites = []
        for site in expected:
            print site
            expected_sites.append(site)
    
        a_job._partition()
        blocks_keys = a_job.blocks_keys

        self.assertEqual(1, len(blocks_keys))
        self.assertEqual(job.Block(expected_sites),
                         job.Block.from_kvs(blocks_keys[0]))

    def test_with_no_partition_we_just_process_a_single_block(self):
        job.SITES_PER_BLOCK = 1
        
        # test exposure has 6 assets
        a_job = Job({EXPOSURE: os.path.join(
                test.DATA_DIR, EXPOSURE_TEST_FILE)})
        
        a_job._partition()
        blocks_keys = a_job.blocks_keys
        
        # but we have 1 block instead of 6
        self.assertEqual(1, len(blocks_keys))


class BlockTestCase(unittest.TestCase):
    
    def test_a_block_has_a_unique_id(self):
        self.assertTrue(job.Block(()).id)
        self.assertTrue(job.Block(()).id != job.Block(()).id)

    def test_can_serialize_a_block_into_kvs(self):
        block = job.Block((SITE, SITE))
        block.to_kvs()

        self.assertEqual(block, job.Block.from_kvs(block.id))

class BlockSplitterTestCase(unittest.TestCase):
    
    def setUp(self):
        self.splitter = None
    
    def test_an_empty_set_produces_no_blocks(self):
        self.splitter = job.BlockSplitter(())
        self._assert_number_of_blocks_is(0)

    def test_splits_the_set_into_a_single_block(self):
        self.splitter = job.BlockSplitter((SITE,), 3)
        self._assert_number_of_blocks_is(1)

        self.splitter = job.BlockSplitter((SITE, SITE), 3)
        self._assert_number_of_blocks_is(1)

        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 3)
        self._assert_number_of_blocks_is(1)

    def test_splits_the_set_into_multiple_blocks(self):
        self.splitter = job.BlockSplitter((SITE, SITE), 1)
        self._assert_number_of_blocks_is(2)

        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 2)
        self._assert_number_of_blocks_is(2)

    def test_generates_the_correct_blocks(self):
        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 3)
        expected_blocks = (job.Block((SITE, SITE, SITE)),)
        self._assert_blocks_are(expected_blocks)

        self.splitter = job.BlockSplitter((SITE, SITE, SITE), 2)
        expected_blocks = (job.Block((SITE, SITE)), job.Block((SITE,)))
        self._assert_blocks_are(expected_blocks)

    def test_splitting_with_region_intersection(self):
        region_constraint = shapes.RegionConstraint.from_simple(
                (0.0, 0.0), (2.0, 2.0))
        
        sites = (shapes.Site(1.0, 1.0), shapes.Site(1.5, 1.5),
            shapes.Site(2.0, 2.0), shapes.Site(3.0, 3.0))

        expected_blocks = (
                job.Block((shapes.Site(1.0, 1.0), shapes.Site(1.5, 1.5))),
                job.Block((shapes.Site(2.0, 2.0),)))

        self.splitter = job.BlockSplitter(sites, 2, constraint=region_constraint)
        self._assert_blocks_are(expected_blocks)

    def _assert_blocks_are(self, expected_blocks):
        for idx, block in enumerate(self.splitter):
            self.assertEqual(expected_blocks[idx], block)

    def _assert_number_of_blocks_is(self, number):
        counter = 0
        
        for block in self.splitter:
            counter += 1
        
        self.assertEqual(number, counter)
