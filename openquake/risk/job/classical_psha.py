#pylint: disable-all
""" Mixin for Classical PSHA Risk Calculation """


class ClassicalPSHABasedMixin:
    """ STUB STUB STUB """
    def store_hazard_curves(self):
        """ Get the regions from the region file and store them in kvs
        """

        # load hazard curve file and write to memcache_client
        # TODO(JMC): Replace this with GMF slicing        
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

    def compute_risk(self, block_id, conditional_loss_poe=None, **kwargs):
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in memcache:
         1) list of sites
         2) hazard curves
         3) exposure portfolio (=assets)
         4) vulnerability

        TODO(fab): make conditional_loss_poe (set of probabilities of exceedance
        for which the loss computation is done) a list of floats, and read it from
        the job configuration.
        """

        if conditional_loss_poe is None:
            conditional_loss_poe = DEFAULT_CONDITIONAL_LOSS_POE

        risk_engine = engines.ClassicalPSHABasedLossRatioCalculator(job_id,
            block_id)

        # TODO(jmc): DONT assumes that hazard, assets, and output risk grid are
        # the same (no nearest-neighbour search to find hazard)
        block = job.Block.from_kvs(block_id)
        sites_list = block.sites

        LOGGER.debug("sites list for job_id %s, block_id %s:\n%s" % (
            job_id, block_id, sites_list))

        for (gridpoint, site) in sites_list:

            logger.debug("processing gridpoint %s, site %s" % (gridpoint, site))
            loss_ratio_curve = risk_engine.compute_loss_ratio_curve(gridpoint)

            if loss_ratio_curve is not None:

                # write to memcache: loss_ratio
                key = kvs.generate_product_key(job_id,
                    risk.LOSS_RATIO_CURVE_KEY_TOKEN, block_id, gridpoint)

                logger.debug("RESULT: loss ratio curve is %s, write to key %s" 
                     % (loss_ratio_curve, key))
                memcache_client.set(key, loss_ratio_curve)
            
                # compute loss curve
                loss_curve = risk_engine.compute_loss_curve(gridpoint, 
                                                            loss_ratio_curve)
                key = kvs.generate_product_key(job_id, 
                    risk.LOSS_CURVE_KEY_TOKEN, block_id, gridpoint)

                logger.debug("RESULT: loss curve is %s, write to key %s" % (
                    loss_curve, key))
                memcache_client.set(key, loss_curve)
            
                # compute conditional loss
                loss_conditional = engines.compute_loss(loss_curve, 
                                                        conditional_loss_poe)
                key = kvs.generate_product_key(job_id, 
                    risk.loss_token(conditional_loss_poe), block_id, gridpoint)

                logger.debug("RESULT: conditional loss is %s, write to key %s"
                    % (loss_conditional, key))
                memcache_client.set(key, loss_conditional)

        # assembling final product needs to be done by jobber, collecting the
        # results from all tasks
        return True
