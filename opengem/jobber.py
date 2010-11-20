# -*- coding: utf-8 -*-
"""
Main jobber module.
"""

import math
import os

from opengem import job
from opengem import flags
from opengem import logs
from opengem import kvs
from opengem import shapes

from opengem.parser import exposure

FLAGS = flags.FLAGS
LOGGER = logs.LOG
SITES_PER_BLOCK = 100

# TODO (ac): This class is not covered by unit tests...
class Jobber(object):
    """The Jobber class is responsible to evaluate the configuration settings
    and to execute the computations in parallel tasks (using the celery
    framework and the message queue RabbitMQ).
    """

    def __init__(self, incoming_job, partition):
        self.memcache_client = None
        self.partition = partition
        self.job = incoming_job
        
        self._init()

    def run(self):
        """Core method of Jobber. It splits the requested computation
        in blocks and executes these as parallel tasks.
        """

        LOGGER.debug("running jobber, job_id = %s" % self.job.id)

        for block_id in self._partition():
            self.job.block_id = block_id
            self.job.launch()

        LOGGER.debug("Jobber run ended")

    def _partition(self):
        """Split the set of sites to compute in blocks and store
        the in the underlying kvs system.
        """

        sites = []
        blocks_keys = []
        region_constraint = self._read_region_constraint()
        
        # we use the exposure, if specified,
        # otherwise we use the input region
        if self.job.has(job.EXPOSURE):
            sites = self._read_sites_from_exposure()
        else:
            sites = shapes.Region.from_file(
                    self.job[job.INPUT_REGION]).sites

        if self.partition:
            for block in BlockSplitter(sites, constraint=region_constraint):
                blocks_keys.append(block.id)
                block.to_kvs()
        else:
            block = Block(sites)
            blocks_keys.append(block.id)
            block.to_kvs()
        
        return blocks_keys

    def _read_region_constraint(self):
        """Read the region constraint, if present, from the job definition."""

        print self.job
        if self.job.has(job.INPUT_REGION):
            return shapes.RegionConstraint.from_file(
                    self.job[job.INPUT_REGION])
        else:
            return None

    def _read_sites_from_exposure(self):
        """Read the set of sites to compute from the exposure file specified
        in the job definition."""

        sites = []
        path = os.path.join(self.job.base_path, self.job[job.EXPOSURE])
        reader = exposure.ExposurePortfolioFile(path)

        
        for asset_data in reader:
            sites.append(asset_data[0])

        return sites

    def _init(self):
        """ Initialize memcached_client. This should move into a Singleton """
        
        # TODO(fab): find out why this works only with binary=False
        self.memcache_client = kvs.get_client(binary=False)


class Block(object):
    """A block is a collection of sites to compute."""

    def __init__(self, sites):
        self.sites = tuple(sites)
        self.block_id = kvs.generate_block_id()

    def __eq__(self, other):
        return self.sites == other.sites

    @classmethod
    def from_kvs(cls, block_id):
        """Return the block in the underlying kvs system with the given id."""

        raw_sites = kvs.get_value_json_decoded(block_id)

        sites = []

        for raw_site in raw_sites:
            sites.append(shapes.Site(raw_site[0], raw_site[1]))

        return Block(sites)

    def to_kvs(self):
        """Store this block into the underlying kvs system."""

        raw_sites = []

        for site in self.sites:
            raw_sites.append(site.coords)

        kvs.set_value_json_encoded(self.id, raw_sites)

    @property
    def id(self):
        """Return the id of this block."""
        return self.block_id


class BlockSplitter(object):
    """Split the sites into a set of blocks."""

    def __init__(self, sites, sites_per_block=SITES_PER_BLOCK, constraint=None):
        self.sites = sites
        self.constraint = constraint
        self.sites_per_block = sites_per_block
    
        if not self.constraint:
            class AlwaysTrueConstraint():
                def match(self, point):
                    return True
            
            self.constraint = AlwaysTrueConstraint()
    
    def __iter__(self):
        if not len(self.sites):
            return

        number_of_blocks = int(math.ceil(len(self.sites) /
                float(self.sites_per_block)))

        for idx in range(number_of_blocks):
            filtered_sites = []
            offset = idx * self.sites_per_block
            sites = self.sites[offset:offset + self.sites_per_block]

            # TODO (ac): Can be done better using shapely.intersects,
            # but after the shapes.Site refactoring...
            for site in sites:
                if self.constraint.match(site):
                    filtered_sites.append(site)
                
            yield(Block(filtered_sites))
