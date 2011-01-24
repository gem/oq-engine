# -*- coding: utf-8 -*-
"""
Collection of functions that compute stuff using
as input data produced with the classical psha method.
"""

from numpy import array # pylint: disable=E1101, E0611
from scipy.stats.mstats import mquantiles

from openquake import kvs
from openquake.logs import LOG


QUANTILE_PARAM_NAME = "QUANTILE_LEVELS"


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


def _acceptable(quantile):
    """Return true if the quantile value taken from the configuration
    file is valid, false otherwise."""
    try:
        quantile = float(quantile)
        return quantile >= 0.0 and quantile <= 1.0

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


def _extract_quantiles_from_config(job):
    """Extract the set of valid quantiles from the configuration file."""
    quantiles = []

    if job.has(QUANTILE_PARAM_NAME):
        raw_quantiles = job.params[QUANTILE_PARAM_NAME].split()
        quantiles = [float(x) for x in raw_quantiles if _acceptable(x)]

    return quantiles


def compute_mean_hazard_curves(job_id, sites):
    """Compute a mean hazard curve for each site in the list
    using as input all the pre computed curves for different realizations."""

    for site in sites:
        mean_curve = {"site_lon": site.longitude, "site_lat": site.latitude,
                "curve": list(compute_mean_curve(curves_at(job_id, site)))}

        key = kvs.tokens.mean_hazard_curve_key(job_id, site)

        LOG.debug("MEAN curve at %s is %s" % (key, mean_curve))

        kvs.set_value_json_encoded(key, mean_curve)


def compute_quantile_hazard_curves(job, sites):
    """Compute a quantile hazard curve for each site in the list
    using as input all the pre computed curves for different realizations.
    
    The QUANTILE_LEVELS parameter in the configuration file specifies
    all the values used in the computation.
    """

    quantiles = _extract_quantiles_from_config(job)

    LOG.debug("List of QUANTILES is %s" % quantiles)

    for site in sites:
        for quantile in quantiles:

            quantile_curve = {"site_lat": site.latitude,
                    "site_lon": site.longitude, "curve":
                    list(compute_quantile_curve(curves_at(
                    job.id, site), quantile))}

            key = kvs.tokens.quantile_hazard_curve_key(
                    job.id, site, quantile)

            LOG.debug("QUANTILE curve at %s is %s" % (key, quantile_curve))

            kvs.set_value_json_encoded(key, quantile_curve)
