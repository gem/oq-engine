# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser

from opengem import kvs

INPUT_REGION = "filter_region"
HAZARD_CURVES = "hazard_curves"
EXPOSURE = "exposure"

RISK_SECTION_NAME = "RISK"
HAZARD_SECTION_NAME = "HAZARD"

class Job(object):
    """A job is a collection of parameters identified by a unique id."""

    @classmethod
    def from_kvs(cls, job_id):
        """Return the job in the underlying kvs system with the given id."""
        
        key = kvs.generate_job_key(job_id)
        kvs_client = kvs.get_client(binary=False)
        params = kvs.get_value_json_decoded(kvs_client, key)

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
            job_id = kvs.generate_random_id()

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
    
    def has(self, name):
        """Return true if this job has the given parameter defined
        and specified, false otherwise."""
        return self.params.has_key(name) and self.params[name] != ""
    
    def __str__(self):
        return str(self.params)

    def validate(self, fn):
        """Validate this job before running the decorated function."""

        def validator(*args):
               try:
                   assert self.has(EXPOSURE) or self.has(INPUT_REGION)
                   return fn(*args)
               except AssertionError:
                   return False

        return validator

    def to_kvs(self):
        """Store this job into the underlying kvs system."""

        key = kvs.generate_job_key(self.job_id)
        kvs_client = kvs.get_client(binary=False)
        kvs.set_value_json_encoded(kvs_client, key, self.params)
