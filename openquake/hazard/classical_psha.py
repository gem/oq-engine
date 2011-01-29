# -*- coding: utf-8 -*-
"""
Collection of functions that compute stuff using
as input data produced with the classical psha method.
"""

import math
from numpy import array # pylint: disable=E1101, E0611
from scipy.interpolate import interp1d # pylint: disable=E1101, E0611
from scipy.stats.mstats import mquantiles

from openquake import kvs
from openquake import shapes
from openquake.logs import HAZARD_LOG


QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"
POES_PARAM_NAME = "POES_HAZARD_MAPS"


def compute_mean_curve(curves):
    """Compute a mean hazard curve.
    
    The input parameter is a list of arrays where each array
    contains just the Y values of the corresponding hazard curve.
    """
    return array(curves).mean(axis=0)


def compute_quantile_curve(curves, quantile):
    """Compute a quantile hazard curve.

    The input parameter is a list of arrays where each array
    contains just the Y values of the corresponding hazard curve.
    """
    result = []

    if len(array(curves).flat):
        result = mquantiles(curves, quantile, axis=0)[0]
    
    return result


def _extract_y_values_from(curve):
    """Extract from a serialized hazard curve (in json format)
    the Y values used to compute the mean hazard curve.
    
    The serialized hazard curve has this format:
    {"site_lon": 1.0, "site_lat": 1.0, "curve": [{"x": 0.1, "y": 0.2}, ...]}
    """
    y_values = []

    for point in curve:
        y_values.append(float(point["y"]))
        
    return y_values


def _acceptable(value):
    """Return true if the value taken from the configuration
    file is valid, false otherwise."""
    try:
        value = float(value)
        return value >= 0.0 and value <= 1.0

    except ValueError:
        return False


def curves_at(job_id, site):
    """Return all the json deserialized hazard curves for
    a single site (different realizations)."""
    pattern = "%s*%s*%s*%s" % (kvs.tokens.HAZARD_CURVE_KEY_TOKEN,
            job_id, site.longitude, site.latitude)

    curves = []
    raw_curves = kvs.mget_decoded(pattern)

    for raw_curve in raw_curves:
        curves.append(_extract_y_values_from(raw_curve["curve"]))
    
    return curves


def _extract_values_from_config(job, param_name):
    """Extract the set of valid quantiles from the configuration file."""
    values = []

    if job.has(param_name):
        raw_values = job.params[param_name].split()
        values = [float(x) for x in raw_values if _acceptable(x)]

    return values


def compute_mean_hazard_curves(job_id, sites):
    """Compute a mean hazard curve for each site in the list
    using as input all the pre computed curves for different realizations."""

    for site in sites:
        mean_curve = {"site_lon": site.longitude, "site_lat": site.latitude,
                "curve": list(compute_mean_curve(curves_at(job_id, site)))}

        key = kvs.tokens.mean_hazard_curve_key(job_id, site)

        HAZARD_LOG.debug("MEAN curve at %s is %s" % (key, mean_curve))

        kvs.set_value_json_encoded(key, mean_curve)


def compute_quantile_hazard_curves(job, sites):
    """Compute a quantile hazard curve for each site in the list
    using as input all the pre computed curves for different realizations.
    
    The QUANTILE_LEVELS parameter in the configuration file specifies
    all the values used in the computation.
    """

    quantiles = _extract_values_from_config(job, QUANTILE_PARAM_NAME)

    HAZARD_LOG.debug("List of QUANTILES is %s" % quantiles)

    for site in sites:
        for quantile in quantiles:

            quantile_curve = {"site_lat": site.latitude,
                    "site_lon": site.longitude, "curve":
                    list(compute_quantile_curve(curves_at(
                    job.id, site), quantile))}

            key = kvs.tokens.quantile_hazard_curve_key(
                    job.id, site, quantile)

            HAZARD_LOG.debug("QUANTILE curve at %s is %s"
                    % (key, quantile_curve))

            kvs.set_value_json_encoded(key, quantile_curve)


def _extract_imls_from_config(job):
    """Return the list of IMLs defined in the configuration file."""
    return [float(x) for x in job.params["INTENSITY_MEASURE_LEVELS"].split()]


def _get_iml_from(mean_curve, job, poe):
    """Return the interpolated IML using as IMLs the values defined in
    the INTENSITY_MEASURE_LEVELS parameter."""
    imls = _extract_imls_from_config(job)
    imls.reverse()
    
    poes = list(mean_curve["curve"])
    poes.reverse()

    site = shapes.Site(mean_curve["site_lon"], mean_curve["site_lat"])

    if poe > poes[-1]:
        HAZARD_LOG.warn("""
For %s asked interpolation of %s but the max POE value is %s,
using the min IML defined (%s)""" % (site, poe, poes[-1], imls[-1]))
        return imls[-1]

    if poe < poes[0]:
        HAZARD_LOG.warn("""
For %s asked interpolation of %s but the min POE value is %s,
using the max IML defined (%s)""" % (site, poe, poes[0], imls[0]))
        return imls[0]

    imls = [math.log(x) for x in imls]
    return math.exp(interp1d(poes, imls)(poe))


def compute_mean_hazard_map(job):
    """Compute a mean hazard map using as input all the
    pre computed mean hazard curves.
    
    The POES_HAZARD_MAPS parameter in the configuration file specifies
    all the values used in the computation.
    """

    poes = _extract_values_from_config(job, POES_PARAM_NAME)

    # get all the computed mean curves
    pattern = "%s*%s*" % (kvs.tokens.MEAN_HAZARD_CURVE_KEY_TOKEN, job.id)
    mean_curves = kvs.mget_decoded(pattern)

    for poe in poes:
        for mean_curve in mean_curves:
            site = shapes.Site(mean_curve["site_lon"], mean_curve["site_lat"])
            key = kvs.tokens.mean_hazard_map_key(job.id, site, poe)
            
            im_level = {}

            im_level["site_lon"] = mean_curve["site_lon"]
            im_level["site_lat"] = mean_curve["site_lat"]
            im_level["vs30"] = job.params["REFERENCE_VS30_VALUE"]
            im_level["IML"] = _get_iml_from(mean_curve, job, poe)
            
            kvs.set_value_json_encoded(key, im_level)
