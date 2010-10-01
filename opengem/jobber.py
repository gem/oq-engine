# -*- coding: utf-8 -*-
"""
Main jobber module
"""

import json
import os
#import pylibmc
import random
import time
import unittest

#from celery.decorators import task

from opengem import identifiers
from opengem import producer
from opengem import shapes

from opengem.logs import HAZARD_LOG, RISK_LOG
#from opengem.memcached import MEMCACHED_PORT, MEMCACHED_HOST
from opengem import memcached
#from opengem.risk import engines

from opengem.risk import tasks

#from opengem.output import geotiff
from opengem.parser import exposure
from opengem.parser import shaml_output
from opengem.parser import vulnerability

from opengem import flags
FLAGS = flags.FLAGS

class Jobber(object):

    def __init__(self, vulnerability_model_file, hazard_curve_file,
                 region_file, exposure_file, output_file, partition):

        print "Jobber.constructor"

        self.vulnerability_model_file = vulnerability_model_file
        self.hazard_curve_file = hazard_curve_file
        self.region_file = region_file
        self.exposure_file = exposure_file
        self.output_file = output_file
        self.partition = partition

        self.memcache_client = None

        self.job_id_generator = identifiers.get_id('job')
        self.block_id_generator = identifiers.get_id('block')

        #print FLAGS

        self._init()

    def run(self):

        job_id = self.job_id_generator.next()
        print "we are inside jobber.run, job_id = %s" % job_id

        #_init()
        
        if self.partition is True:
            self._partition(job_id)
        else:
            block_id = self.block_id_generator.next()
            self._preload(job_id, block_id)
            self._execute(job_id, block_id)

        print "Jobber run ended, bye bye"

    def _partition(self, job_id):
        pass

    def _execute(self, job_id, block_id):
        
        # execute celery task for risk, for given block with sites
        print "starting task block, block_id = %s" % block_id

        result = tasks.compute_risk.apply_async(args=[job_id, block_id])
        result.get()
        
        print "task finished"

    def _init(self):
        
        # memcached
        # TODO(fab): find out why this works only with binary=False
        self.memcache_client = memcached.get_client(binary=False)
        self.memcache_client.flush_all()

    def _preload(self, job_id, block_id):

        # set region
        print "setting region"
        region_constraint = shapes.RegionConstraint.from_file(self.region_file)
        region_constraint.cell_size = 1.0

        # load hazard curve file and write to memcache_client
        print "loading hazard curves"
        shaml_parser = shaml_output.ShamlOutputFile(self.hazard_curve_file)
        attribute_constraint = \
            producer.AttributeConstraint({'IMT' : 'MMI'})

        sites_hash_list = []

        HAZARD_LOG.debug("Going to parse hazard curves")

        for site, hazard_curve_data in shaml_parser.filter(
                region_constraint, attribute_constraint):

            gridpoint = region_constraint.grid.point_at(site)

            # store site hashes in memcache
            # TODO(fab): separate this from hazard curves
            sites_hash_list.append(str(gridpoint))

            hazard_curve = shapes.FastCurve(zip(hazard_curve_data['IML'], 
                                                hazard_curve_data['Values']))

            memcache_key_hazard = identifiers.get_product_key(
                job_id, block_id, gridpoint, "hazard_curve")

            success = self.memcache_client.set(memcache_key_hazard, 
                hazard_curve.to_json())

            if success is not True:
                raise ValueError(
                    "jobber: cannot write hazard curve to memcache")
            
            HAZARD_LOG.debug("Loading hazard curve %s at %s, %s" % (
                        hazard_curve, site.latitude,  site.longitude))
            #print "wrote hazard curve for site %s" % gridpoint

        # write site hashes to memcache (JSON)
        memcache_key_sites = identifiers.get_product_key(
                job_id, block_id, None, "sites")
        success = memcached.set_value_json_encoded(self.memcache_client, 
                memcache_key_sites, sites_hash_list)
        if not success:
            raise ValueError(
                "jobber: cannot write sites to memcache")
        
        # load assets and write to memcache
        print "loading assets"
        exposure_parser = exposure.ExposurePortfolioFile(self.exposure_file)
        for site, asset in exposure_parser.filter(region_constraint):
            gridpoint = region_constraint.grid.point_at(site)

            memcache_key_asset = identifiers.get_product_key(
                job_id, block_id, gridpoint, "exposure")
            success = memcached.set_value_json_encoded(self.memcache_client, 
                memcache_key_asset, asset)
            if not success:
                raise ValueError(
                    "jobber: cannot write asset to memcache")

            print "Loading asset %s at %s, %s" % (asset,
                site.latitude,  site.longitude)
            RISK_LOG.debug("Loading asset %s at %s, %s" % (asset,
                site.latitude,  site.longitude))

        # load vulnerability and write to memcache
        print "loading vulnerability"
        vulnerability.load_vulnerability_model(job_id,
            self.vulnerability_model_file)
