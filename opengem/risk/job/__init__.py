""" Mixin proxy for risk jobs, and associated
Risk Job Mixin decorators """

from opengem.job.mixins import Mixin


def output(fn):
    """ Decorator for output """
    def output_writer(self, *args, **kwargs):
        """ Write the output of a block to memcached. """
        result = fn(self, *args, **kwargs)

        # TODO(chris): Should we use the returned result?
        if result:
            # pylint: disable-msg=W0212
            _write_output_for_block(self.job_id, self.block_id)
        return result

    return output_writer


def _write_output_for_block(job_id, block_id):
    """note: this is usable only for one block"""
    
    # produce output for one block
    loss_curves = []

    sites = kvs.get_sites_from_memcache(job_id, block_id)

    for (gridpoint, (site_lon, site_lat)) in sites:
        key = kvs.generate_product_key(job_id, 
            risk.LOSS_CURVE_KEY_TOKEN, block_id, gridpoint)
        loss_curve = kvs.get_value_json_decoded(key)
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


class RiskJobMixin(Mixin):
    """ A mixin proxy for Risk jobs """
    mixins = {}

Mixin.register("Risk", RiskJobMixin, order=2)
