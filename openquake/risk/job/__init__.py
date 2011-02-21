# -*- coding: utf-8 -*-
""" Mixin proxy for risk jobs, and associated
Risk Job Mixin decorators """

import json
import os

from openquake.output import geotiff
from openquake import job
from openquake.job import mixins
from openquake import kvs 
from openquake import logs
from openquake import shapes
from openquake.output import curve
from openquake.output import risk as risk_output

from celery.decorators import task

LOG = logs.LOG


@task
def compute_risk(job_id, block_id, **kwargs):
    """ A task for computing risk, calls the mixed in compute_risk method """
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, RiskJobMixin, key="risk") as mixed:
        mixed.compute_risk(block_id, **kwargs)


class RiskJobMixin(mixins.Mixin):
    """ A mixin proxy for Risk jobs """
    mixins = {}
    
    def _write_output_for_block(self, job_id, block_id):
        """ Given a job and a block, write out a plotted curve """
        decoder = json.JSONDecoder()
        loss_ratio_curves = []
        block = job.Block.from_kvs(block_id)
        for point in block.grid(self.region):
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [decoder.decode(x) for x in asset_list]:
                site = shapes.Site(asset['lon'], asset['lat'])
                key = kvs.tokens.loss_ratio_key(
                        job_id, point.row, point.column, asset["assetID"])
                loss_ratio_curve = kvs.get(key)
                if loss_ratio_curve:
                    loss_ratio_curve = shapes.Curve.from_json(loss_ratio_curve)
                    loss_ratio_curves.append((site, (loss_ratio_curve, asset)))

        LOG.debug("Serializing loss_ratio_curves")
        filename = "%s-block-%s.xml" % (
            self['LOSS_CURVES_OUTPUT_PREFIX'], block_id)
        path = os.path.join(self.base_path, self['OUTPUT_DIR'], filename)
        output_generator = risk_output.LossRatioCurveXMLWriter(path)
        # TODO(JMC): Take mean or max for each site
        output_generator.serialize(loss_ratio_curves)
        
        filename = "%s-block-%s.svg" % (
            self['LOSS_CURVES_OUTPUT_PREFIX'], block_id)
        curve_path = os.path.join(self.base_path, self['OUTPUT_DIR'], filename)

        plotter = curve.RiskCurvePlotter(curve_path, path, 
            mode='loss_ratio')
        plotter.plot(autoscale_y=False)
        
        results = [path]
        results.extend(list(plotter.filenames()))
        return results
    
    def write_loss_map(self, loss_poe):
        """ Iterates through all the assets and maps losses at loss_poe """
        decoder = json.JSONDecoder()
        # Make a special grid at a higher resolution
        risk_grid = shapes.Grid(self.region, float(self['RISK_CELL_SIZE']))
        filename = "losses_at-%s.tiff" % (loss_poe)
        path = os.path.join(self.base_path, self['OUTPUT_DIR'], filename) 
        output_generator = geotiff.LossMapGeoTiffFile(path, risk_grid, 
                init_value=0.0, normalize=True)
        for point in self.region.grid:
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [decoder.decode(x) for x in asset_list]:
                key = kvs.tokens.loss_key(self.id, point.row, point.column, 
                        asset["assetID"], loss_poe)
                loss = kvs.get(key)
                LOG.debug("Loss for asset %s at %s %s is %s" % 
                    (asset["assetID"], asset['lon'], asset['lat'], loss))
                if loss:
                    loss_ratio = float(loss) / float(asset["assetValue"])
                    risk_site = shapes.Site(asset['lon'], asset['lat'])
                    risk_point = risk_grid.point_at(risk_site)
                    output_generator.write(
                            (risk_point.row, risk_point.column), loss_ratio)
        output_generator.close()
        return [path]


mixins.Mixin.register("Risk", RiskJobMixin, order=2)
