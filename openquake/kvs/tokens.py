# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""Tokens for KVS keys."""

import hashlib

from openquake import logs


LOG = logs.LOG

KVS_KEY_SEPARATOR = '!'

# hazard tokens
SOURCE_MODEL_TOKEN = 'sources'
GMPE_TOKEN = 'gmpe'
ERF_KEY_TOKEN = 'erf'
MGM_KEY_TOKEN = 'mgm'
HAZARD_CURVE_POES_KEY_TOKEN = 'hazard_curve_poes'
MEAN_HAZARD_CURVE_KEY_TOKEN = 'mean_hazard_curve'
QUANTILE_HAZARD_CURVE_KEY_TOKEN = 'quantile_hazard_curve'
STOCHASTIC_SET_TOKEN = 'ses'
MEAN_HAZARD_MAP_KEY_TOKEN = 'mean_hazard_map'
QUANTILE_HAZARD_MAP_KEY_TOKEN = 'quantile_hazard_map'
GMFS_KEY_TOKEN = 'GMFS'

# risk tokens
CONDITIONAL_LOSS_KEY_TOKEN = 'LOSS_AT'
EXPOSURE_KEY_TOKEN = 'ASSET'
GMF_KEY_TOKEN = 'GMF'
LOSS_RATIO_CURVE_KEY_TOKEN = 'LOSS_RATIO_CURVE'
LOSS_CURVE_KEY_TOKEN = 'LOSS_CURVE'
VULNERABILITY_CURVE_KEY_TOKEN = 'VULNERABILITY_CURVE'


CURRENT_JOBS = 'CURRENT_JOBS'


def generate_key(*parts):
    """ Create a kvs key """
    parts = [str(x).replace(" ", "") for x in parts]
    return KVS_KEY_SEPARATOR.join(parts)

JOB_KEY_FMT = '::JOB::%s::'


def generate_job_key(job_id):
    """
    Return a job key if the following format:
    ::JOB::<job_id>::

    :param int job_id: job ID
    """
    return JOB_KEY_FMT % job_id


def generate_blob_key(job_id, blob):
    """ Return the KVS key for a binary blob """
    return generate_key(generate_job_key(job_id),
                        hashlib.sha1(blob).hexdigest())


def loss_token(poe):
    """ Return a loss token made up of the CONDITIONAL_LOSS_KEY_TOKEN and
    the poe cast to a string """
    return "%s%s" % (CONDITIONAL_LOSS_KEY_TOKEN, str(poe))


def vuln_key(job_id):
    """Generate the key used to store vulnerability curves."""
    return generate_key(generate_job_key(job_id), "VULN_CURVES")


def asset_key(job_id, row, col):
    """ Return an asset key """
    return generate_key(generate_job_key(job_id), row, col,
                        EXPOSURE_KEY_TOKEN)


def source_model_key(job_id):
    """ Return the KVS key for the source model of the given job"""
    return generate_key(generate_job_key(job_id), SOURCE_MODEL_TOKEN)


def gmpe_key(job_id):
    """ Return the KVS key for the GMPE of the given job"""
    return generate_key(generate_job_key(job_id), GMPE_TOKEN)


def stochastic_set_key(job_id, history, realization):
    """ Return the KVS key for the given job and stochastic set"""
    return generate_key(generate_job_key(job_id), STOCHASTIC_SET_TOKEN,
                        history, realization)


def erf_key(job_id):
    """ Return the KVS key for the ERF of the given job"""
    return generate_key(generate_job_key(job_id), ERF_KEY_TOKEN)


def mgm_key(job_id, block_id, site_id):
    """ Return the KVS key for the MGM of the given job, block and site"""
    return generate_key(generate_job_key(job_id), MGM_KEY_TOKEN, block_id,
                        site_id)


def asset_row_col_from_kvs_key(kvs_key):
    """
    Extract row and column from a key of type EXPOSURE_KEY_TOKEN
    :param:kvs_key: the key
    :type:kvs_key: string

    :returns: a tuple (job_id, row, col) if the key is of type
        EXPOSURE_KEY_TOKEN, None otherwise
    """

    payload, _sep, type_ = kvs_key.rpartition(KVS_KEY_SEPARATOR)

    if type_ == EXPOSURE_KEY_TOKEN:
        job_id, row, col = payload.split(KVS_KEY_SEPARATOR)
        return job_id, int(row), int(col)
    else:
        return None


def loss_ratio_key(job_id, row, col, asset_id):
    """ Return a loss ratio key  """
    return generate_key(generate_job_key(job_id), row, col,
                        LOSS_RATIO_CURVE_KEY_TOKEN, asset_id)


def loss_curve_key(job_id, row, col, asset_id):
    """ Return a loss curve key """
    return generate_key(generate_job_key(job_id), row, col,
                        LOSS_CURVE_KEY_TOKEN, asset_id)


def loss_key(job_id, row, col, asset_id, poe):
    """ Return a loss key """
    return generate_key(generate_job_key(job_id), row, col, loss_token(poe),
                        asset_id)


def _mean_hazard_curve_key(job_id, site_fragment):
    "Common code for the key functions below"
    return generate_key(MEAN_HAZARD_CURVE_KEY_TOKEN, generate_job_key(job_id),
                        site_fragment)


def mean_hazard_curve_key(job_id, site):
    """Return the key used to store a mean hazard curve for a single site.

    :param job_id: the id of the job.
    :type job_id: integer
    :param site: site where the curve is computed.
    :type site: :py:class:`shapes.Site` object
    :returns: the key.
    :rtype: string
    """
    return _mean_hazard_curve_key(job_id, hash(site))


def mean_hazard_curve_key_template(job_id):
    """Return a template for a key used to store a mean hazard curve for a
    single site.

    The template must be specialized before use with something similar to:
    `template_key % hash(site)`

    :param job_id: the id of the job.
    :type job_id: integer
    :returns: the key.
    :rtype: string
    """
    return _mean_hazard_curve_key(job_id, '%s')


def _quantile_hazard_curve_key(job_id, site_fragment, quantile):
    "Common code for the key functions below"
    return generate_key(QUANTILE_HAZARD_CURVE_KEY_TOKEN,
                        generate_job_key(job_id), site_fragment, str(quantile))


def quantile_hazard_curve_key(job_id, site, quantile):
    """Return the key used to store a quantile hazard curve for a single site.

    :param job_id: the id of the job.
    :type job_id: integer
    :param site: site where the curve is computed.
    :type site: :py:class:`shapes.Site` object
    :param quantile: quantile used to compute the curve.
    :type quantile: float
    :returns: the key.
    :rtype: string
    """

    return _quantile_hazard_curve_key(job_id, hash(site), quantile)


def quantile_hazard_curve_key_template(job_id, quantile):
    """Return a template for a key used to store a quantile hazard curve for a
    single site.

    The template must be specialized before use with something similar to:
    `template_key % hash(site)`

    :param job_id: the id of the job.
    :type job_id: integer
    :param quantile: quantile used to compute the curve.
    :type quantile: float
    :returns: the key.
    :rtype: string
    """

    return _quantile_hazard_curve_key(job_id, '%s', quantile)


def _mean_hazard_map_key(job_id, site_fragment, poe):
    "Common code for the key functions below"
    return generate_key(MEAN_HAZARD_MAP_KEY_TOKEN, generate_job_key(job_id),
                        site_fragment, str(poe))


def mean_hazard_map_key(job_id, site, poe):
    """Return the key used to store the interpolated IML
    (Intensity Measure Level) used in mean hazard maps for a single site.

    :param job_id: the id of the job.
    :type job_id: integer
    :param site: site where the value is computed.
    :type site: :py:class:`shapes.Site` object
    :param poe: probability of exceedance used to compute the value.
    :type poe: float
    :returns: the key.
    :rtype: string
    """

    return _mean_hazard_map_key(job_id, hash(site), poe)


def mean_hazard_map_key_template(job_id, poe):
    """Return a template key used to store the interpolated IML (Intensity
    Measure Level) used in mean hazard maps for a single site.

    The template must be specialized before use with something similar to:
    `template_key % hash(site)`

    :param job_id: the id of the job.
    :type job_id: integer
    :param poe: probability of exceedance used to compute the value.
    :type poe: float
    :returns: the key.
    :rtype: string
    """

    return _mean_hazard_map_key(job_id, '%s', poe)


def _quantile_hazard_map_key(job_id, site_fragment, poe, quantile):
    "Common code for the key functions below"
    return generate_key(QUANTILE_HAZARD_MAP_KEY_TOKEN,
                        generate_job_key(job_id), site_fragment, str(poe),
                        str(quantile))


def quantile_hazard_map_key(job_id, site, poe, quantile):
    """Return the key used to store the interpolated IML
    (Intensity Measure Level) used in quantile hazard maps for a single site.

    :param job_id: the id of the job.
    :type job_id: integer
    :param site: site where the value is computed.
    :type site: :py:class:`shapes.Site` object
    :param poe: probability of exceedance used to compute the value.
    :type poe: float
    :param quantile: quantile used to compute the curve.
    :type quantile: float
    :returns: the key.
    :rtype: string
    """
    return _quantile_hazard_map_key(job_id, hash(site), poe, quantile)


def quantile_hazard_map_key_template(job_id, poe, quantile):
    """Return a template key used to store the interpolated IML (Intensity
    Measure Level) used in quantile hazard maps for a single site.

    The template must be specialized before use with something similar to:
    `template_key % hash(site)`

    :param job_id: the id of the job.
    :type job_id: integer
    :param poe: probability of exceedance used to compute the value.
    :type poe: float
    :param quantile: quantile used to compute the curve.
    :type quantile: float
    :returns: the key.
    :rtype: string
    """
    return _quantile_hazard_map_key(job_id, '%s', poe, quantile)


def _hazard_curve_poes_key(job_id, realization_num, site_fragment):
    "Common code for the key functions below"
    return generate_key(HAZARD_CURVE_POES_KEY_TOKEN, generate_job_key(job_id),
                        realization_num, site_fragment)


def hazard_curve_poes_key(job_id, realization_num, site):
    """ Result a hazard curve key (for a single site) """

    return _hazard_curve_poes_key(job_id, realization_num, hash(site))


def hazard_curve_poes_key_template(job_id, realization_num):
    """ Result a template for a hazard curve key (for a single site) """
    return _hazard_curve_poes_key(job_id, realization_num, '%s')


def _kvs_key_type(kvs_key):
    """
    Given a KVS key, extract its type.  For example, given a key for a mean
    hazard map, the string 'mean_hazard_map' will be returned.

    :param kvs_key: kvs product key
    :type kvs_key: str

    :returns: type portion of the key
    """
    return kvs_key.split(KVS_KEY_SEPARATOR, 2)[1]


def gmf_set_key(job_id, column, row):
    """Return the key used to store a ground motion field set for a single
    site."""
    return generate_key(generate_job_key(job_id), GMF_KEY_TOKEN, column, row)


def column_row_from_gmf_set_key(kvs_key):
    """Extract column and row from a KVS key of a ground motion field set."""
    assert _kvs_key_type(kvs_key) == GMF_KEY_TOKEN

    return kvs_key.split(KVS_KEY_SEPARATOR)[2:]


def ground_motion_values_key(job_id, point):
    """
    Return the key used to store multiple realizations of ground motion
    values for a single point in the grid.

    :param job_id: the id of the job.
    :type job_id: integer
    :param point: grid location of the GMF data
    :type point: :py:class:`shapes.GridPoint` object
    :returns: the key.
    :rtype: string
    """

    return generate_key(generate_job_key(job_id), GMFS_KEY_TOKEN,
                        point.column, point.row)
