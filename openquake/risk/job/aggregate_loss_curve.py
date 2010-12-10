# -*- coding: utf-8 -*-
"""
# TODO (ac): Document
"""

import os

from openquake import shapes
from openquake.output import curve
from openquake.risk import probabilistic_event_based as prob

# TODO (ac): Move and use also the job id!
KVS_KEY = "aggregated_curve"

def filename(job_id):
    return "%s-aggregate-loss-curve.svg" % job_id

# TODO (ac): Document
def for_plotting(curve):
    data = {}
    
    data["AggregatedLossCurve"] = {}
    data["AggregatedLossCurve"]["abscissa"] = tuple(curve.abscissae)
    data["AggregatedLossCurve"]["ordinate"] = tuple(curve.ordinates)
    data["AggregatedLossCurve"]["abscissa_property"] = "Losses"
    data["AggregatedLossCurve"]["ordinate_property"] = "PoEs"
    data["AggregatedLossCurve"]["curve_title"] = "Aggregated Loss Curve"
    
    return data

class AggregateLossCurveMixin:
    
    def tses(self):
        histories = int(self.params["NUMBER_OF_SEISMICITY_HISTORIES"])
        realizations = int(self.params["NUMBER_OF_HAZARD_CURVE_CALCULATIONS"])
        
        num_ses = histories * realizations
        return num_ses * self.time_span()

    def time_span(self):
        return float(self.params["INVESTIGATION_TIME"])

    def execute(self):
        curves = shapes.CurveSet.from_kvs(KVS_KEY)
        aggregate_loss_curve = prob.AggregateLossCurve.from_curve_set(curves)
        
        path = os.path.join(self.base_path,
                self.params["OUTPUT_DIR"], filename(self.id))

        plotter = curve.CurvePlot(path)
        plotter.write(for_plotting(aggregate_loss_curve.compute(
                self.tses(), self.time_span())), autoscale_y=False)

        plotter.close()
