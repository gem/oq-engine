# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser

from opengem import memcached
from opengem import identifiers

INPUT_REGION = "filter_region"
HAZARD_CURVES = "hazard_curves"

RISK_SECTION_NAME = "RISK"
HAZARD_SECTION_NAME = "HAZARD"

class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    @classmethod
    def from_memcached(cls, job_id):
        """Return the job in memcached with the given id."""
        
        key = identifiers.MEMCACHE_KEY_SEPARATOR.join(("JOB", str(job_id)))
        memcached_client = memcached.get_client(binary=False)
        params = memcached.get_value_json_decoded(memcached_client, key)

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

        parser = ConfigParser()
        parser.read([risk_config_file, hazard_config_file])

        params = {}

        # risk parameters
        for param in parser.items(RISK_SECTION_NAME):
            params[param[0]] = param[1]

        # hazard parameters
        for param in parser.items(HAZARD_SECTION_NAME):
            params[param[0]] = param[1]

        return Job(params)

    def __init__(self, params, job_id=None):
        
        if job_id is None:
            job_id = identifiers.generate_sequence().next()

        self.job_id = job_id
        self.params = params

    @property
    def id(self):
        """Return the id of this job."""
        return self.job_id

    def __getitem__(self, name):
        return self.params[name]

    def __eq__(self, other):
        return self.params == other.params
        
    def __str__(self):
        return str(self.params)

    def to_memcached(self):
        """Store this job into memcached."""

        key = identifiers.MEMCACHE_KEY_SEPARATOR.join(
                ("JOB", str(self.job_id)))

        memcached_client = memcached.get_client(binary=False)
        memcached.set_value_json_encoded(memcached_client, key, self.params)
