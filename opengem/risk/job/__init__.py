""" Mixin proxy for risk jobs, and associated
Risk Job Mixin decorators """


from opengem import job
from opengem.job import mixins
from opengem import kvs 
from opengem import risk

from celery.decorators import task


def output(fn):
    """ Decorator for output """
    def output_writer(self, *args, **kwargs):
        """ Write the output of a block to memcached. """
        result = fn(self, *args, **kwargs)
        if result:
            for block_id in self.blocks_keys:
                _write_output_for_block(self.job_id, self.block_id)
        return result

    return output_writer


@task
def compute_risk(job_id, block_id, **kwargs):
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, RiskJobMixin, key="risk") as mixed:
        mixed.compute_risk(block_id, **kwargs)
        

class RiskJobMixin(mixins.Mixin):
    """ A mixin proxy for Risk jobs """
    mixins = {}
    
    def _write_output_for_block(self, job_id, block_id):
        """note: this is usable only for one block"""
        loss_curves = []

        block = job.Block.from_kvs(block_id)
        sites_list = block.sites
        for site in sites_list:
            gridpoint = self.region.grid.point_at(site)
            key = kvs.generate_product_key(job_id, 
                risk.LOSS_CURVE_KEY_TOKEN, gridpoint.column, gridpoint.row)
            loss_curve = kvs.get_value_json_decoded(key)
            loss_curves.append((site, loss_curve))

        LOGGER.debug("serializing loss_curves")
        filename = "%s-block-%s.xml" % (
            self['LOSS_CURVES_OUTPUT_PREFIX'], block_id)
        path = os.path.join(self.base_path, filename)
        output_generator = RiskXMLWriter(path)
        output_generator.serialize(loss_curves)
    
        #output_generator = output.SimpleOutput()
        #output_generator.serialize(ratio_results)
    
        #output_generator = geotiff.GeoTiffFile(output_file, 
        #    region_constraint.grid)
        #output_generator.serialize(losses_one_perc)

mixins.Mixin.register("Risk", RiskJobMixin, order=2)
