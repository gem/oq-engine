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

from openquake.risk.job.aggregate_loss_curve import AggregateLossCurveMixin

from celery.decorators import task

LOG = logs.LOG

def output(fn):
    """ Decorator for output """
    def output_writer(self, *args, **kwargs):
        """ Write the output of a block to kvs. """
        fn(self, *args, **kwargs)
        conditional_loss_poes = [float(x) for x in self.params.get(
                    'CONDITIONAL_LOSS_POE', "0.01").split()]
        #if result:
        results = []
        for block_id in self.blocks_keys:
            #pylint: disable=W0212
            results.extend(self._write_output_for_block(self.job_id, block_id))
        for loss_poe in conditional_loss_poes:
            results.extend(self.write_loss_map(loss_poe))
        return results

    return output_writer


def _serialize(path, **kwargs):
    """ Serialize the curves """
    LOG.debug("Serializing %s" % kwargs['curve_mode'])
    # TODO(JMC): Take mean or max for each site
    if kwargs["curve_mode"] == "loss_ratio": 
        output_generator = risk_output.LossRatioCurveXMLWriter(path)
    elif kwargs["curve_mode"] == 'loss':
        output_generator = risk_output.LossCurveXMLWriter(path)
    output_generator.serialize(kwargs['curves'])
    return path


def _plot(curve_path, result_path, **kwargs):
    """
    Build a plotter, and then render the plot
    """
    LOG.debug("Plotting %s" % kwargs['curve_mode'])

    render_multi = kwargs.get("render_multi")
    autoscale = False if kwargs['curve_mode'] == 'loss_ratio' else True
    plotter = curve.RiskCurvePlotter(result_path,
                                     curve_path,
                                     mode=kwargs["curve_mode"],
                                     render_multi=render_multi)
    plotter.plot(autoscale_y=autoscale) 
    return plotter.filenames()


@task
def compute_risk(job_id, block_id, **kwargs):
    """ A task for computing risk, calls the mixed in compute_risk method """
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, RiskJobMixin, key="risk") as mixed:
        mixed.compute_risk(block_id, **kwargs)
        

class RiskJobMixin(mixins.Mixin):
    """ A mixin proxy for Risk jobs """
    mixins = {}

    def _serialize_and_plot(self, block_id, **kwargs):
        """
        Build filename/paths for serializing/plotting and call _serialize
        and then _plot. Return the list of filenames.
        """

        if kwargs['curve_mode'] == 'loss_ratio': 
            serialize_filename = "%s-block-%s.xml" % (
                                     self["LOSS_CURVES_OUTPUT_PREFIX"],
                                     block_id)
        elif kwargs['curve_mode'] == 'loss':
            serialize_filename = "%s-loss-block-%s.xml" % (
                                     self["LOSS_CURVES_OUTPUT_PREFIX"],
                                     block_id)

        serialize_path = os.path.join(self.base_path,
                                      self['OUTPUT_DIR'],
                                      serialize_filename)
        results = [_serialize(serialize_path, **kwargs)]

        curve_filename = "%s-block-%s.svg" % (
                                self['LOSS_CURVES_OUTPUT_PREFIX'], block_id)
        curve_results_path = os.path.join(self.base_path,
                                          self['OUTPUT_DIR'],
                                          curve_filename)

        results.extend(_plot(serialize_path, curve_results_path, **kwargs))
        return results
    
    def _write_output_for_block(self, job_id, block_id):
        """ Given a job and a block, write out a plotted curve """
        loss_ratio_curves = []
        loss_curves = []
        block = job.Block.from_kvs(block_id)
        for point in block.grid(self.region):
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.loads(x) for x in asset_list]:
                site = shapes.Site(asset['lon'], asset['lat'])
                
                loss_curve = kvs.get(
                                kvs.tokens.loss_curve_key(job_id,
                                                          point.row,
                                                          point.column,
                                                          asset["assetID"]))
                loss_ratio_curve = kvs.get(
                                kvs.tokens.loss_ratio_key(job_id,
                                                          point.row,
                                                          point.column,
                                                          asset["assetID"]))

                if loss_curve:
                    loss_curve = shapes.Curve.from_json(loss_curve)
                    loss_curves.append((site, (loss_curve, asset)))

                if loss_ratio_curve:
                    loss_ratio_curve = shapes.Curve.from_json(loss_ratio_curve)
                    loss_ratio_curves.append((site, (loss_ratio_curve, asset)))


        results = self._serialize_and_plot(block_id, 
                                           curves=loss_ratio_curves,
                                           curve_mode='loss_ratio')
        results.extend(self._serialize_and_plot(block_id, 
                                                curves=loss_curves,
                                                curve_mode='loss', 
                                                curve_mode_prefix='loss_curve',
                                                render_multi=True))
        return results
    
    def write_loss_map(self, loss_poe):
        """ Iterates through all the assets and maps losses at loss_poe """
        # Make a special grid at a higher resolution
        risk_grid = shapes.Grid(self.region, float(self['RISK_CELL_SIZE']))
        path = os.path.join(self.base_path,
                            self['OUTPUT_DIR'],
                            "losses_at-%s.tiff" % loss_poe) 
        output_generator = geotiff.LossMapGeoTiffFile(path, risk_grid, 
                init_value=0.0, normalize=True)
        for point in self.region.grid:
            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.loads(x) for x in asset_list]:
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
mixins.Mixin.register("AggregateLossCurve", AggregateLossCurveMixin, order=3)
