# -*- coding: utf-8 -*-

""" A single hazard/risk job """

import hashlib
import re
import os

from ConfigParser import ConfigParser

from opengem import kvs
from opengem.logs import LOG
from opengem.job.mixins import Mixin


INPUT_REGION = "filter_region"
HAZARD_CURVES = "hazard_curves"
RE_INCLUDE = re.compile(r'^(.*)_include')

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
            # Handle includes.
            if RE_INCLUDE.match(key):
                config_file = "%s/%s" % (os.path.dirname(config_file), value)
                params.update(parse_config_file(config_file))
            else:
                params[key.upper()] = value

    return params


class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    @staticmethod
    def from_memcached(job_id):
        """Return the job in memcached with the given id."""
        
        key = kvs.generate_job_key(job_id)
        memcached_client = kvs.get_client(binary=False)
        params = kvs.get_value_json_decoded(memcached_client, key)

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
        self.params = params
        self.base_path = base_path
        if base_path:
            self.to_memcached()
        
    @property
    def id(self):
        """Return the id of this job."""
        return self.job_id
    
    @property
    def key(self):
        """Returns the kvs key for this job."""
        return kvs.generate_job_key(self.job_id)

    def launch(self):
        for mixin in Mixin.mixins():
            with Mixin(self.__class__, mixin):
                # The mixin defines a preload decorator to handle the needed
                # data for the tasks and decorates _execute(). the mixin's
                # _execute() method calls the expected tasks.
                self.execute()

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
            raise Exception("Can't slurp files without a base path, homie...")
        for key, val in self.params.items():
            if key[-5:] == '_FILE':
                LOG.debug("Slurping %s : %s" % (key, val))
                path = os.path.join(self.base_path, val)
                with open(path) as data_file:
                    LOG.debug("Slurping %s" % path)
                    sha1 = hashlib.sha1(data_file.read()).hexdigest()
                    data_file.seek(0)
                    memcached_client.set(sha1, data_file.read())
                    self.params[key] = sha1

    def to_memcached(self):
        """Store this job into memcached."""
        # self._slurp_files()
        key = kvs.generate_job_key(self.job_id)
        memcached_client = kvs.get_client(binary=False)
        kvs.set_value_json_encoded(memcached_client, key, self.params)
