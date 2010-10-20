# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser, NoOptionError

from opengem import memcached
from opengem import identifiers

JOB_ID = "JOB_ID"
INPUT_REGION = "filter_region"
HAZARD_CURVES = "hazard_curves"

RISK_SECTION_NAME = "RISK"
HAZARD_SECTION_NAME = "HAZARD"

class Config(object):
    """Reads configuration files and generates jobs."""
    
    @classmethod
    def job_with_id(cls, job_id):
        """Return the job in memcached with the given id."""
        
        memcached_client = memcached.get_client(binary=False)
        key = "JOB%s%s" % (identifiers.MEMCACHE_KEY_SEPARATOR, job_id)
        return memcached.get_value_json_decoded(memcached_client, key)

    def __init__(self, risk_config_file, hazard_config_file):
        self.parser = ConfigParser()
        self.parser.read([risk_config_file, hazard_config_file])

    def __getitem__(self, name):
        try:
            return self.parser.get(HAZARD_SECTION_NAME, name)
        except NoOptionError:
            try:
                return self.parser.get(RISK_SECTION_NAME, name)
            except NoOptionError:
                raise ValueError("Parameter %s unknown!", name)

    def generate_job(self, job_id=None):
        """Generate a job with the loaded parameters."""
        
        if job_id is None:
            job_id = identifiers.generate_sequence().next()
        
        job = {}
        
        # risk parameters
        for param in self.parser.items(RISK_SECTION_NAME):
            job[param[0]] = param[1]
        
        # hazard parameters
        for param in self.parser.items(HAZARD_SECTION_NAME):
            job[param[0]] = param[1]
        
        job[JOB_ID] = identifiers.MEMCACHE_KEY_SEPARATOR.join(
                ("JOB", str(job_id)))

        return job

    def generate_and_store_job(self, job_id=None):
        """Generate a job and store it in memcached."""
        
        job = self.generate_job(job_id)
        memcached_client = memcached.get_client(binary=False)
        memcached.set_value_json_encoded(memcached_client, job[JOB_ID], job)
        
        return job

    @property
    def risk(self):
        """Return the parameters defined in the risk configuration file."""
        return self.parser.items(RISK_SECTION_NAME)

    @property
    def hazard(self):
        """Return the parameters defined in the hazard configuration file."""
        return self.parser.items(HAZARD_SECTION_NAME)