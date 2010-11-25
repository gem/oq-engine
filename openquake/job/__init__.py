# -*- coding: utf-8 -*-

""" A single hazard/risk job """

import hashlib
import re
import os

from ConfigParser import ConfigParser

from openquake import kvs
from openquake.logs import LOG
from openquake.job.mixins import Mixin


EXPOSURE = "EXPOSURE"
INPUT_REGION = "FILTER_REGION"
HAZARD_CURVES = "HAZARD_CURVES"
RE_INCLUDE = re.compile(r'^(.*)_INCLUDE')

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
            assert self.has(EXPOSURE) or self.has(INPUT_REGION)
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
        self.block_id = 10
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

    @validate
    def launch(self):
        """ Based on the behaviour specified in the configuration, mix in the
        correct behaviour for the tasks and then execute them.
        """

        results = []
        for (key, mixin) in Mixin.ordered_mixins():
            with Mixin(self, mixin, key=key):
                # The mixin defines a preload decorator to handle the needed
                # data for the tasks and decorates _execute(). the mixin's
                # _execute() method calls the expected tasks.
                results.append(self.execute())

        return results

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
