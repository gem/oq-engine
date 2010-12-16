# -*- coding: utf-8 -*-

""" A single hazard/risk job """

import hashlib
import math
import os
import re
import urlparse

from ConfigParser import ConfigParser, RawConfigParser

from openquake import kvs
from openquake import shapes
from openquake.logs import LOG
from openquake.job.handlers import resolve_handler
from openquake.job.mixins import Mixin
from openquake.parser import exposure


EXPOSURE = "EXPOSURE"
INPUT_REGION = "FILTER_REGION"
HAZARD_CURVES = "HAZARD_CURVES"
RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')
SITES_PER_BLOCK = 100


def run_job(job_file):
    """ Given a job_file, run the job. If we don't get results log it """
    a_job = Job.from_file(job_file)
    # TODO(JMC): Expose a way to set whether jobs should be partitioned
    results = a_job.launch()
    if not results:
        LOG.critical("The job configuration is inconsistent, "
                "aborting computation.")
    else:
        for filepath in results:
            print filepath


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
            # TODO(JMC): Add good stuff here
            assert self.has(EXPOSURE) or self.has(INPUT_REGION)
        except AssertionError, e:
            LOG.exception(e)
            return []
        return fn(self, *args)

    return validator


def guarantee_file(base_path, file_spec):
    """Resolves a file_spec (http, local relative or absolute path, git url,
    etc.) to an absolute path to a (possibly temporary) file."""

    url = urlparse.urlparse(file_spec)
    return resolve_handler(url, base_path).get()


class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    __default_configs = [os.path.join(os.path.dirname(__file__),
                            "../", "default.gem"), #package
                         "opengem.gem",        # Sane Defaults
                         "/etc/opengem.gem",   # Site level configs
                         "~/.opengem.gem"]     # Are we running as a user?

    @staticmethod
    def from_kvs(job_id):
        """Return the job in the underlying kvs system with the given id."""
        
        params = kvs.get_value_json_decoded(kvs.generate_job_key(job_id))
        return Job(params, job_id)

    @staticmethod
    def from_file(config_file):
        """ Create a job from external configuration files. """
        config_file = os.path.abspath(config_file)
        LOG.debug("Loading Job from %s" % (config_file)) 
        
        base_path = os.path.abspath(os.path.dirname(config_file))
        params = {}
        for each_config_file in Job.__default_configs + [config_file]:
            params.update(parse_config_file(each_config_file))
        params['BASE_PATH'] = base_path
        job = Job(params, base_path=base_path)
        job.config_file = config_file               #pylint: disable-msg=W0201
        # job.config_file = job.super_config_path   #pylint: disable-msg=W0201
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
    def id(self): #pylint: disable-msg=C0103
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

    @property
    def super_config_path(self):
        """ Return the path of the super config """
        filename = "%s-super.gem" % self.job_id
        return os.path.join(self.base_path or '', "./", filename)

    @validate
    def launch(self):
        """ Based on the behaviour specified in the configuration, mix in the
        correct behaviour for the tasks and then execute them.
        """
        output_dir = os.path.join(self.base_path, self['OUTPUT_DIR'])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        results = []
        self._partition()
        for (key, mixin) in Mixin.ordered_mixins():
            with Mixin(self, mixin, key=key):
                # The mixin defines a preload decorator to handle the needed
                # data for the tasks and decorates _execute(). the mixin's
                # _execute() method calls the expected tasks.
                LOG.debug("Job %s Launching %s for %s" % (self.id, mixin, key)) 
                results.extend(self.execute()) #pylint: disable-msg=E1101

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
            LOG.debug("Loaded %s sites from exposure portfolio." % len(sites))
        elif self.region:
            sites = self.region.sites
        else:
            raise Exception("I don't know how to get the sites!")
        if self.partition:
            block_count = 0
            for block in BlockSplitter(sites, constraint=region_constraint):
                self.blocks_keys.append(block.id)
                block.to_kvs()
                block_count += 1
            LOG.debug("Job has partitioned %s sites into %s blocks" % (
                    len(sites), block_count))
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
        else:
            LOG.debug("Constraining exposure parsing to %s" % 
                constraint.polygon)
        for asset_data in reader.filter(constraint):
            sites.append(asset_data[0])

        return sites

    def __getitem__(self, name):
        return self.params[name]

    def __eq__(self, other):
        return self.params == other.params
        
    def __str__(self):
        return str(self.params)

    def _write_super_config(self):
        """
            Take our params and write them out as a 'super' config file. 
            Its name is equal to the job_id, which should be the sha1 of
            the file in production or a random job in dev.
        """

        kvs_client = kvs.get_client(binary=False)
        config = RawConfigParser()

        section = 'openquake'
        config.add_section(section)

        for key, val in self.params.items():
            v = kvs_client.get(val)
            if v:
                val = v
            config.set(section, key, val)

        with open(self.super_config_path, "wb") as configfile:
            config.write(configfile)

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

    def to_kvs(self, write_cfg=True):
        """Store this job into memcached."""
        self._slurp_files()
        if write_cfg:
            self._write_super_config()
        key = kvs.generate_job_key(self.job_id)
        kvs.set_value_json_encoded(key, self.params)


class AlwaysTrueConstraint():
    """ A stubbed constraint for block splitting """

    #pylint: disable-msg=W0232,W0613,R0201
    def match(self, point):
        """ stub a match filter to always return true """
        return True


class Block(object):
    """A block is a collection of sites to compute."""

    def __init__(self, sites, block_id=None):
        self.sites = tuple(sites)
        if not block_id:
            block_id = kvs.generate_block_id()
        self.block_id = block_id

    def grid(self, region):
        """Provides an iterator across the unique grid points within a region,
         corresponding to the sites within this block."""
        used_points = []
        for site in self.sites:
            point = region.grid.point_at(site)
            if point not in used_points:
                used_points.append(point)
                yield point

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
    def id(self): #pylint: disable-msg=C0103
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
        filtered_sites = []

        for site in self.sites:
            if self.constraint.match(site):
                filtered_sites.append(site)
                if len(filtered_sites) == self.sites_per_block:
                    yield(Block(filtered_sites))
                    filtered_sites = []
        if not filtered_sites:
            return    
        yield(Block(filtered_sites))
