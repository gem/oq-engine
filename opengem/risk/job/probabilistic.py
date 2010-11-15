# pylint: disable-msg=W0232

""" Probabilistic Event Mixin: 

    Defines the behaviour of a Job. Calls the compute_risk task

"""

from celery.exceptions import TimeoutError

from opengem import hazard
from opengem import job
from opengem import kvs
from opengem import logs
from opengem import producer
from opengem import risk
from opengem import settings
from opengem import shapes

from opengem.output.risk import RiskXMLWriter
from opengem.parser import exposure
from opengem.parser import hazard
from opengem.parser import vulnerability
from opengem.risk import tasks
from opengem.risk.job import preload, output, RiskJobMixin


LOGGER = logs.LOG


class ProbabilisticEventMixin:
    """ Mixin for Probalistic Event Risk Job """

    @preload
    @output
    def execute(self):
        """ Execute a ProbabilisticLossRatio Job """
        
        LOGGER.debug("starting task block, block_id = %s" % self.block_id)

        # task compute_risk has return value 'True' (writes its results to
        # memcache).

        # pylint: disable-msg=E1101
        task = tasks.compute_risk.apply_async(args=[self.id, 
                                                    self.block_id])

        try:
            # TODO(chris): Figure out where to put that timeout.
            return task.wait(timeout=None)
        except TimeoutError:
            return None

    def _write_output_for_block(self, job_id, block_id):
        """note: this is usable only for one block"""
        
        # produce output for one block
        loss_curves = []

        sites = kvs.get_sites_from_memcache(job_id, block_id)

        for (gridpoint, (site_lon, site_lat)) in sites:
            key = kvs.generate_product_key(job_id, 
                risk.LOSS_CURVE_KEY_TOKEN, block_id, gridpoint)
            loss_curve = self.memcache_client.get(key)
            loss_curves.append((shapes.Site(site_lon, site_lat), 
                                loss_curve))

        LOGGER.debug("serializing loss_curves")
        output_generator = RiskXMLWriter(settings.LOSS_CURVES_OUTPUT_FILE)
        output_generator.serialize(loss_curves)
        
        #output_generator = output.SimpleOutput()
        #output_generator.serialize(ratio_results)
        
        #output_generator = geotiff.GeoTiffFile(output_file, 
        #    region_constraint.grid)
        #output_generator.serialize(losses_one_perc)

    def store_region_constraint(self):
        # pylint: disable-msg=W0201
        """ set region
        If there's a region file, use it. Otherwise,
        get the region of interest as the convex hull of the
        multipoint collection of the portfolio of assets.
        """

        region = self.params[job.INPUT_REGION]
        filter_cell_size = self.params.get("filter cell size", 1.0)
        self.region_constraint = shapes.RegionConstraint.from_file(
            self.base_path + region)
        self.region_constraint.cell_size = filter_cell_size

    def store_sites_and_hazard_curve(self):
        """ Get the regions from the region file and store them in memcached
        """

        # load hazard curve file and write to memcache_client

        nrml_parser = hazard.NrmlFile("%s/%s" % (self.base_path,
            self.params[job.HAZARD_CURVES]))
        attribute_constraint = producer.AttributeConstraint({'IMT' : 'MMI'})
        sites_hash_list = []

        for site, hazard_curve_data in \
            nrml_parser.filter(self.region_constraint, attribute_constraint):

            gridpoint = self.region_constraint.grid.point_at(site)

            # store site hashes in memcache
            # TODO(fab): separate this from hazard curves. Regions of interest
            # should not be taken from hazard curve input, should be 
            # idependent from the inputs (hazard, exposure)
            sites_hash_list.append((str(gridpoint), 
                                   (site.longitude, site.latitude)))

            hazard_curve = shapes.Curve(zip(hazard_curve_data['IML'], 
                                                hazard_curve_data['Values']))

            memcache_key_hazard = kvs.generate_product_key(self.id,
                hazard.HAZARD_CURVE_KEY_TOKEN, self.block_id, gridpoint)

            LOGGER.debug("Loading hazard curve %s at %s, %s" % (
                        hazard_curve, site.latitude,  site.longitude))

            success = self.memcache_client.set(memcache_key_hazard, 
                hazard_curve.to_json())

            if not success:
                raise ValueError(
                    "jobber: cannot write hazard curve to memcache")

        # write site hashes to memcache (JSON)
        memcache_key_sites = kvs.generate_sites_key(self.id, self.block_id)

        success = kvs.set_value_json_encoded(memcache_key_sites, 
            sites_hash_list)
        if not success:
            raise ValueError("jobber: cannot write sites to memcache")

    def store_exposure_assets(self):
        """ Load exposure assets and write to memcache """
        
        exposure_parser = exposure.ExposurePortfolioFile("%s/%s" % 
            (self.base_path, self.params[job.EXPOSURE]))

        for site, asset in exposure_parser.filter(self.region_constraint):
            gridpoint = self.region_constraint.grid.point_at(site)

            memcache_key_asset = kvs.generate_product_key(
                self.id, risk.EXPOSURE_KEY_TOKEN, self.block_id, gridpoint)

            LOGGER.debug("Loading asset %s at %s, %s" % (asset,
                site.longitude,  site.latitude))

            success = kvs.set_value_json_encoded(memcache_key_asset, asset)
            if not success:
                raise ValueError(
                    "jobber: cannot write asset to memcache")

    def store_vulnerability_model(self):
        """ load vulnerability and write to memcache """
        vulnerability.load_vulnerability_model(self.id,
            "%s/%s" % (self.base_path, self.params["VULNERABILITY"]))


RiskJobMixin.register("Probabilistic Event", ProbabilisticEventMixin)
