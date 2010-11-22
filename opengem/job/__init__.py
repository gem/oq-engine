# -*- coding: utf-8 -*-

""" A single hazard/risk job """

import hashlib
import math
import re
import os

from ConfigParser import ConfigParser

from opengem import kvs
from opengem import shapes
from opengem.logs import LOG
from opengem.job.mixins import Mixin
from opengem.parser import exposure


EXPOSURE = "EXPOSURE"
INPUT_REGION = "FILTER_REGION"
HAZARD_CURVES = "HAZARD_CURVES"
RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')
SITES_PER_BLOCK = 100


def parse_config_file(config_file):
    """
    We have a single configuration file which may contain a risk section and
    a hazard section. This input file must be in the ConfigParser format
    defined at: http://docs.python.org/library/configparser.html.

    There may be a general section which may define configuration includes in
    the format of "sectionname_include = someconfigname.gem". These too must be
    in the ConfigParser format.
    """

    parser = ConfigParser()
    parser.read(config_file)

    params = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            key = key.upper()
            # Handle includes.
            if RE_INCLUDE.match(key):
                config_file = "%s/%s" % (os.path.dirname(config_file), value)
                params.update(parse_config_file(config_file))
            else:
                params[key] = value

    return params


def validate(fn):
    """Validate this job before running the decorated function."""

    def validator(self, *args):
        """Validate this job before running the decorated function."""
        try:
            # assert self.has(EXPOSURE) or self.has(INPUT_REGION)
            return fn(self, *args)
        except AssertionError:
            return False

    return validator


def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""
    # TODO(JMC): Parse out git, http, or full paths here...
    return os.path.join(base_path, file_spec)


class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    @staticmethod
    def from_kvs(job_id):
        """Return the job in the underlying kvs system with the given id."""
        
        params = kvs.get_value_json_decoded(kvs.generate_job_key(job_id))
        return Job(params, job_id)

    @staticmethod
    def from_file(config_file):
        """ Create a job from external configuration files. """
        
        base_path = os.path.dirname(config_file)
        params = parse_config_file(config_file)

        job = Job(params, base_path=base_path)
        job.config_file = config_file
        return job

    def __init__(self, params, job_id=None, base_path=None):
        if job_id is None:
            job_id = kvs.generate_random_id()
        
        self.job_id = job_id
        self.blocks_keys = []
        self.partition = True
        self.params = params
        self.base_path = base_path
        if base_path:
            self.to_kvs()

    def has(self, name):
        """Return true if this job has the given parameter defined
        and specified, false otherwise."""
        return self.params.has_key(name) and self.params[name] != ""

    @property
    def id(self):
        """Return the id of this job."""
        return self.job_id
    
    @property
    def key(self):
        """Returns the kvs key for this job."""
        return kvs.generate_job_key(self.job_id)

    @property
    def region(self):
        """Compute valid region with appropriate cell size from config file."""
        if not self.has('REGION_VERTEX'):
            return None
        verts = [float(x) for x in self['REGION_VERTEX'].split(",")]
        # Flips lon and lat, and builds a list of coord tuples
        coords = zip(verts[1::2], verts[::2])
        region = shapes.RegionConstraint.from_coordinates(coords)
        region.cell_size = float(self['REGION_GRID_SPACING'])
        return region

    @validate
    def launch(self):
        """ Based on the behaviour specified in the configuration, mix in the
        correct behaviour for the tasks and then execute them.
        """
        
        results = []
        self._partition()
        for (key, mixin) in Mixin.ordered_mixins():
            with Mixin(self, mixin, key=key):
                # The mixin defines a preload decorator to handle the needed
                # data for the tasks and decorates _execute(). the mixin's
                # _execute() method calls the expected tasks.
                results.append(self.execute())

        return results

    def _partition(self):
        """Split the set of sites to compute in blocks and store
        the in the underlying kvs system.
        """

        sites = []
        self.blocks_keys = []
        region_constraint = self.region
        
        # we use the exposure, if specified,
        # otherwise we use the input region
        if self.has(EXPOSURE):
            sites = self._read_sites_from_exposure()
        elif self.region:
            sites = self.region.sites
        else:
            raise Exception("I don't know how to get the sites!")

        if self.partition:
            for block in BlockSplitter(sites, constraint=region_constraint):
                self.blocks_keys.append(block.id)
                block.to_kvs()
        else:
            block = Block(sites)
            self.blocks_keys.append(block.id)
            block.to_kvs()

    def _read_sites_from_exposure(self):
        """Read the set of sites to compute from the exposure file specified
        in the job definition."""

        sites = []
        path = os.path.join(self.base_path, self[EXPOSURE])
        reader = exposure.ExposurePortfolioFile(path)
        constraint = self.region
        if not constraint:
            constraint = AlwaysTrueConstraint()
        for asset_data in reader.filter(constraint):
            sites.append(asset_data[0])

        return sites

    def __getitem__(self, name):
        return self.params[name]

    def __eq__(self, other):
        return self.params == other.params
        
    def __str__(self):
        return str(self.params)
    
    def _slurp_files(self):
        """Read referenced files and write them into memcached, key'd on their
        sha1s."""
        memcached_client = kvs.get_client(binary=False)
        if self.base_path is None:
            LOG.debug("Can't slurp files without a base path, homie...")
            return
            # raise Exception("Can't slurp files without a base path, homie...")
        for key, val in self.params.items():
            if key[-5:] == '_FILE':
                path = os.path.join(self.base_path, val)
                with open(path) as data_file:
                    LOG.debug("Slurping %s" % path)
                    sha1 = hashlib.sha1(data_file.read()).hexdigest()
                    data_file.seek(0)
                    memcached_client.set(sha1, data_file.read())
                    self.params[key] = sha1

    def to_kvs(self):
        """Store this job into memcached."""
        self._slurp_files()
        key = kvs.generate_job_key(self.job_id)
        kvs.set_value_json_encoded(key, self.params)


class AlwaysTrueConstraint():
    def match(self, point):
        return True


class Block(object):
    """A block is a collection of sites to compute."""

    def __init__(self, sites, block_id=None):
        self.sites = tuple(sites)
        if not block_id:
            block_id = kvs.generate_block_id()
        self.block_id = block_id

    def __eq__(self, other):
        return self.sites == other.sites

    @classmethod
    def from_kvs(cls, block_id):
        """Return the block in the underlying kvs system with the given id."""

        raw_sites = kvs.get_value_json_decoded(block_id)

        sites = []

        for raw_site in raw_sites:
            sites.append(shapes.Site(raw_site[0], raw_site[1]))

        return Block(sites, block_id)

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
            self.constraint = AlwaysTrueConstraint()
    
    def __iter__(self):
        if not len(self.sites):
            yield(Block())
            return

        filtered_sites = []

        # TODO (ac): Can be done better using shapely.intersects,
        # but after the shapes.Site refactoring...
        for site in self.sites:
            if self.constraint.match(site):
                filtered_sites.append(site)
                if len(filtered_sites) == self.sites_per_block:
                    yield(Block(filtered_sites))
                    filtered_sites = []
        if not filtered_sites:
            return    
        yield(Block(filtered_sites))
