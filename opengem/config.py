# -*- coding: utf-8 -*-

import hashlib
import os

from ConfigParser import ConfigParser

from opengem import kvs
from opengem.logs import LOG

INPUT_REGION = "filter_region"
HAZARD_CURVES = "hazard_curves"

RISK_SECTION_NAME = "RISK"
HAZARD_SECTION_NAME = "HAZARD"

class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    @classmethod
    def from_memcached(cls, job_id):
        """Return the job in memcached with the given id."""
        
        key = kvs.generate_job_key(job_id)
        memcached_client = kvs.get_client(binary=False)
        params = kvs.get_value_json_decoded(memcached_client, key)

        return Job(params, job_id)

    @classmethod
    def from_files(cls, risk_config_file, hazard_config_file):
        """Create a job from external configuration files.
        
        We have a configuration file for the risk part, and a configuration
        file for the hazard part. The input files must be compatible with the
        ConfigParser module, http://docs.python.org/library/configparser.html.
        
        The risk parameters must be defined under the [RISK] section,
        while the hazard parameters must be defined under the [HAZARD] section.

        """
        
        base_path = os.path.dirname(risk_config_file)

        parser = ConfigParser()
        parser.read([risk_config_file, hazard_config_file])

        params = {}

        # risk parameters
        for param in parser.items(RISK_SECTION_NAME):
            params[str(param[0]).upper()] = param[1]

        # hazard parameters
        for param in parser.items(HAZARD_SECTION_NAME):
            params[str(param[0]).upper()] = param[1]

        return Job(params, base_path=base_path)

    def __init__(self, params, job_id=None, base_path=None):
        
        if job_id is None:
            job_id = kvs.generate_random_id()
        
        self.job_id = job_id
        self.params = params
        self.base_path = base_path
        
    @property
    def id(self):
        """Return the id of this job."""
        return self.job_id
    
    @property
    def key(self):
        """Returns the kvs key for this job."""
        return kvs.generate_job_key(self.job_id)

    def __getitem__(self, name):
        return self.params[name]

    def __eq__(self, other):
        return self.params == other.params
        
    def __str__(self):
        return str(self.params)

    def _slurp_files(self):
        """Read referenced files and write them into memcached, key'd on their
        sha1s."""
        memcached_client = kvs.get_client(binary=True)
        if self.base_path is None:
            raise Exception("Can't slurp files without a base path, homie...")
        for key, val in self.params.items():
            if key[-5:] == '_FILE':
                LOG.debug("Slurping %s : %s" % (key, val))
                path = os.path.join(self.base_path, val)
                with open(path) as data_file:
                    LOG.debug("Slurping %s" % path)
                    sha1 = hashlib.sha1(data_file.read()).hexdigest()
                    LOG.debug("SHA1 is %s" % sha1)
                    data_file.seek(0)
                    memcached_client.set(sha1, data_file.read())
                    self.params[key] = sha1

    def to_memcached(self):
        """Store this job into memcached."""
        self._slurp_files()
        key = kvs.generate_job_key(self.job_id)
        memcached_client = kvs.get_client(binary=False)
        kvs.set_value_json_encoded(memcached_client, key, self.params)
