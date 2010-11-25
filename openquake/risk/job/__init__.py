""" Mixin proxy for risk jobs, and associated
Risk Job Mixin decorators """

import os

from openquake import job
from openquake.job import mixins
from openquake import kvs 
from openquake import logs
from openquake import risk
from openquake import shapes
from openquake.output import risk as risk_output

from celery.decorators import task

LOG = logs.LOG

def output(fn):
    """ Decorator for output """
    def output_writer(self, *args, **kwargs):
        """ Write the output of a block to memcached. """
        fn(self, *args, **kwargs)
        #if result:
        results = []
        for block_id in self.blocks_keys:
            results.extend(self._write_output_for_block(self.job_id, block_id))
        return results

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
            loss_curve = shapes.Curve.from_json(kvs.get(key))
            loss_curves.append((site, loss_curve))

        LOG.debug("Serializing loss_curves")
        filename = "%s-block-%s.xml" % (
            self['LOSS_CURVES_OUTPUT_PREFIX'], block_id)
        path = os.path.join(self.base_path, filename)
        output_generator = risk_output.RiskXMLWriter(path)
        output_generator.serialize(loss_curves)
        return [path]
        
        #output_generator = output.SimpleOutput()
        #output_generator.serialize(ratio_results)
    
        #output_generator = geotiff.GeoTiffFile(output_file, 
        #    region_constraint.grid)
        #output_generator.serialize(losses_one_perc)

mixins.Mixin.register("Risk", RiskJobMixin, order=2)
