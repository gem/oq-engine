# -*- coding: utf-8 -*-

# Copyright (c) 2010-2013, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""Tokens for KVS keys."""

import hashlib


_KVS_KEY_SEPARATOR = '!'

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
BLOCK_KEY_TOKEN = "BLOCK"
CONDITIONAL_LOSS_KEY_TOKEN = 'LOSS_AT'
EXPOSURE_KEY_TOKEN = 'ASSET'
GMF_KEY_TOKEN = 'GMF'
LOSS_RATIO_CURVE_KEY_TOKEN = 'LOSS_RATIO_CURVE'
LOSS_CURVE_KEY_TOKEN = 'LOSS_CURVE'
VULNERABILITY_CURVE_KEY_TOKEN = 'VULNERABILITY_CURVE'
BCR_BLOCK_KEY_TOKEN = 'BCR_BLOCK'


CURRENT_JOBS = 'CURRENT_JOBS'


def _generate_key(job_id, type_, *parts):
    """
    Create a kvs key
    :param job_id: the job id
    :type job_id: int
    :param type_: the key type
    :param type_: string
    :returns: the KVS key
    :rtype: string
    """
    parts = [generate_job_key(job_id), type_] + [str(p) for p in parts]
    return _KVS_KEY_SEPARATOR.join(parts).replace(' ', '')


def _kvs_key_type(kvs_key):
    """
    Given a KVS key, extract its type.  For example, given a key for a mean
    hazard map, the string 'mean_hazard_map' will be returned.

    :param kvs_key: kvs product key
    :type kvs_key: str

    :returns: type portion of the key
    """
    return kvs_key.split(_KVS_KEY_SEPARATOR, 2)[1]


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
    return _generate_key(job_id, 'blob', hashlib.sha1(blob).hexdigest())


def vuln_key(job_id, retrofitted=False):
    """Generate the key used to store vulnerability curves."""
    return _generate_key(job_id, "VULN_CURVES",
                         "retrofitted" if retrofitted else "normal")


def source_model_key(job_id):
    """ Return the KVS key for the source model of the given job"""
    return _generate_key(job_id, SOURCE_MODEL_TOKEN)


def gmpe_key(job_id):
    """ Return the KVS key for the GMPE of the given job"""
    return _generate_key(job_id, GMPE_TOKEN)


def stochastic_set_key(job_id, history, realization):
    """ Return the KVS key for the given job and stochastic set"""
    return _generate_key(job_id, STOCHASTIC_SET_TOKEN, history, realization)


def erf_key(job_id):
    """ Return the KVS key for the ERF of the given job"""
    return _generate_key(job_id, ERF_KEY_TOKEN)


def mgm_key(job_id, block_id, site_id):
    """ Return the KVS key for the MGM of the given job, block and site"""
    return _generate_key(job_id, MGM_KEY_TOKEN, block_id, site_id)


def asset_row_col_from_kvs_key(kvs_key):
    """
    Extract row and column from a key of type EXPOSURE_KEY_TOKEN
    :param:kvs_key: the key
    :type:kvs_key: string

    :returns: a tuple (row, col)
    """
    assert _kvs_key_type(kvs_key) == EXPOSURE_KEY_TOKEN

    row, col = kvs_key.rsplit(_KVS_KEY_SEPARATOR, 2)[-2:]

    return int(row), int(col)


def risk_block_key(job_id, block_index):
    """ Return the key for a risk block """
    return _generate_key(job_id, BLOCK_KEY_TOKEN, block_index)


def loss_ratio_key(job_id, row, col, asset_id):
    """ Return a loss ratio key  """
    return _generate_key(job_id, LOSS_RATIO_CURVE_KEY_TOKEN, asset_id,
                         row, col)


def loss_curve_key(job_id, row, col, asset_id, retrofitted=False):
    """ Return a loss curve key """
    return _generate_key(job_id, LOSS_CURVE_KEY_TOKEN, asset_id, row, col,
                         "retrofitted" if retrofitted else "normal")


def loss_key(job_id, row, col, asset_id, poe):
    """ Return a loss key """
    return _generate_key(job_id, CONDITIONAL_LOSS_KEY_TOKEN, asset_id, poe,
                         row, col)


def bcr_block_key(job_id, block_id):
    """ Return a BCR block result key """
    return _generate_key(job_id, BCR_BLOCK_KEY_TOKEN, block_id)


def _mean_hazard_curve_key(job_id, site_fragment):
    "Common code for the key functions below"
    return _generate_key(job_id, MEAN_HAZARD_CURVE_KEY_TOKEN, site_fragment)


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
    return _generate_key(job_id, QUANTILE_HAZARD_CURVE_KEY_TOKEN,
                         site_fragment, str(quantile))


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
    return _generate_key(job_id, MEAN_HAZARD_MAP_KEY_TOKEN, site_fragment,
                         str(poe))


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
    return _generate_key(job_id, QUANTILE_HAZARD_MAP_KEY_TOKEN,
                         site_fragment, str(poe), str(quantile))


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
    return _generate_key(job_id, HAZARD_CURVE_POES_KEY_TOKEN, realization_num,
                         site_fragment)


def hazard_curve_poes_key(job_id, realization_num, site):
    """ Result a hazard curve key (for a single site) """

    return _hazard_curve_poes_key(job_id, realization_num, hash(site))


def hazard_curve_poes_key_template(job_id, realization_num):
    """ Result a template for a hazard curve key (for a single site) """
    return _hazard_curve_poes_key(job_id, realization_num, '%s')


def gmf_set_key(job_id, column, row):
    """Return the key used to store a ground motion field set for a single
    site."""
    return _generate_key(job_id, GMF_KEY_TOKEN, column, row)


def column_row_from_gmf_set_key(kvs_key):
    """Extract column and row from a KVS key of a ground motion field set."""
    assert _kvs_key_type(kvs_key) == GMF_KEY_TOKEN

    return kvs_key.split(_KVS_KEY_SEPARATOR)[2:]


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

    return _generate_key(job_id, GMFS_KEY_TOKEN, point.column, point.row)
