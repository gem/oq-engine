# Copyright (c) 2010-2014, GEM Foundation.
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

"""
Functionality for exporting and serializing hazard curve calculation results.
"""


import os
import csv

from collections import namedtuple

from openquake.hazardlib.calc import disagg
from openquake.commonlib import hazard_writers
from openquake.commonlib.writers import floatformat

from openquake.engine.db import models
from openquake.engine.export import core


def _get_result_export_dest(calc_id, target, result, file_ext='xml'):
    """
    Get the full absolute path (including file name) for a given ``result``.

    As a side effect, intermediate directories are created such that the file
    can be created and written to immediately.

    :param int calc_id:
        ID of the associated
        :class:`openquake.engine.db.models.OqJob`.
    :param target:
        Destination directory location for exported files OR a file-like
        object. If file-like, we just simply return it.
    :param result:
        :mod:`openquake.engine.db.models` result object with a foreign key
        reference to :class:`~openquake.engine.db.models.Output`.
    :param file_ext:
        Desired file extension for the output file.
        Defaults to 'xml'.

    :returns:
        Full path (including filename) to the destination export file.
        If the ``target`` is a file-like, we don't do anything special
        and simply return it.
    """
    if not isinstance(target, (basestring, buffer)):
        # It's not a file path. In this case, we expect a file-like object.
        # Just return it.
        return target

    output = result.output
    output_type = output.output_type

    # Create the names for each subdirectory
    calc_dir = 'calc_%s' % calc_id
    type_dir = output_type

    imt_dir = ''  # if blank, we don't have an IMT dir
    if output_type in ('hazard_curve', 'hazard_map', 'disagg_matrix'):
        imt_dir = result.imt
        if result.imt == 'SA':
            imt_dir = 'SA-%s' % result.sa_period

    # construct the directory which will contain the result XML file:
    directory = os.path.join(target, calc_dir, type_dir, imt_dir)
    core.makedirs(directory)

    if output_type in ('hazard_curve', 'hazard_curve_multi', 'hazard_map',
                       'uh_spectra'):
        # include the poe in hazard map and uhs file names
        if output_type in ('hazard_map', 'uh_spectra'):
            output_type = '%s-poe_%s' % (output_type, result.poe)

        if result.statistics is not None:
            # we could have stats
            if result.statistics == 'quantile':
                # quantile
                filename = '%s-%s.%s' % (output_type,
                                         'quantile_%s' % result.quantile,
                                         file_ext)
            else:
                # mean
                filename = '%s-%s.%s' % (output_type, result.statistics,
                                         file_ext)
        else:
            # otherwise, we need to include logic tree branch info
            ltr = result.lt_realization
            sm_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.sm_lt_path)
            gsim_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.gsim_lt_path)
            if ltr.weight is None:
                # Monte-Carlo logic tree sampling
                filename = '%s-smltp_%s-gsimltp_%s-ltr_%s.%s' % (
                    output_type, sm_ltp, gsim_ltp, ltr.ordinal, file_ext
                )
            else:
                # End Branch Enumeration
                filename = '%s-smltp_%s-gsimltp_%s.%s' % (
                    output_type, sm_ltp, gsim_ltp, file_ext
                )
    elif output_type == 'gmf':
        # only logic trees, no stats
        ltr = result.lt_realization
        sm_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.sm_lt_path)
        gsim_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.gsim_lt_path)
        if ltr.weight is None:
            # Monte-Carlo logic tree sampling
            filename = '%s-smltp_%s-gsimltp_%s-ltr_%s.%s' % (
                output_type, sm_ltp, gsim_ltp, ltr.ordinal, file_ext
            )
        else:
            # End Branch Enumeration
            filename = '%s-smltp_%s-gsimltp_%s.%s' % (
                output_type, sm_ltp, gsim_ltp, file_ext
            )
    elif output_type == 'ses':
        sm_ltp = core.LT_PATH_JOIN_TOKEN.join(result.sm_lt_path)
        filename = '%s-%s-smltp_%s.%s' % (
            output_type, result.ordinal, sm_ltp, file_ext
        )
    elif output_type == 'disagg_matrix':
        # only logic trees, no stats

        out = '%s(%s)' % (output_type, result.poe)
        location = 'lon_%s-lat_%s' % (result.location.x, result.location.y)

        ltr = result.lt_realization
        sm_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.sm_lt_path)
        gsim_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.gsim_lt_path)
        if ltr.weight is None:
            # Monte-Carlo logic tree sampling
            filename = '%s-%s-smltp_%s-gsimltp_%s-ltr_%s.%s' % (
                out, location, sm_ltp, gsim_ltp, ltr.ordinal, file_ext
            )
        else:
            # End Branch Enumeration
            filename = '%s-%s-smltp_%s-gsimltp_%s.%s' % (
                out, location, sm_ltp, gsim_ltp, file_ext
            )
    else:
        filename = '%s.%s' % (output_type, file_ext)

    return os.path.abspath(os.path.join(directory, filename))


@core.export_output.add(('hazard_curve', 'xml'),
                        ('hazard_curve', 'geojson'))
def export_hazard_curve(key, output, target):
    """
    Export the specified hazard curve ``output`` to the ``target``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `hazard_curve`.
    :param target:
        The same ``target`` as :func:`export`.
    :returns:
        The same return value as defined by :func:`export`.
    """
    export_type = key[1]
    hc = models.HazardCurve.objects.get(output=output.id)
    hcd = _curve_data(hc)
    metadata = _curve_metadata(output, target)
    haz_calc = output.oq_job
    dest = _get_result_export_dest(
        haz_calc.id, target, hc, file_ext=export_type)
    writercls = hazard_writers.HazardCurveGeoJSONWriter \
        if export_type == 'geojson' else hazard_writers.HazardCurveXMLWriter
    writercls(dest, **metadata).serialize(hcd)
    return dest


@core.export_output.add(('hazard_curve', 'csv'))
def export_hazard_curve_csv(key, output, target):
    """
    Save a hazard curve (of a given IMT) as a .csv file in the format
    (lon lat poe1 ... poeN), where the fields are space separated.
    """
    hc = models.HazardCurve.objects.get(output=output.id)
    haz_calc_id = output.oq_job.id
    dest = _get_result_export_dest(haz_calc_id, target, hc, file_ext='csv')
    x_y_poes = models.HazardCurveData.objects.all_curves_simple(
        filter_args=dict(hazard_curve=hc.id))
    with open(dest, 'wb') as f:
        writer = csv.writer(f, delimiter=' ')
        for x, y, poes in sorted(x_y_poes):
            writer.writerow([x, y] + poes)
    return dest


@core.export_output.add(('hazard_curve_multi', 'xml'))
def export_hazard_curve_multi_xml(key, output, target):
    hcs = output.hazard_curve

    data = [_curve_data(hc) for hc in hcs]

    metadata_set = []
    for hc in hcs:
        metadata = _curve_metadata(hc.output, target)
        metadata_set.append(metadata)

    haz_calc = output.oq_job
    dest = _get_result_export_dest(haz_calc.id, target, hcs)

    writer = hazard_writers.MultiHazardCurveXMLWriter(dest, metadata_set)
    writer.serialize(data)

    return dest


def _curve_metadata(output, target):
    hc = models.HazardCurve.objects.get(output=output.id)
    if hc.lt_realization is not None:
        # If the curves are for a specified logic tree realization,
        # get the tree paths
        lt_rlz = hc.lt_realization
        smlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsimlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)
    else:
        # These curves must be statistical aggregates
        smlt_path = None
        gsimlt_path = None

    return {
        'quantile_value': hc.quantile,
        'statistics': hc.statistics,
        'smlt_path': smlt_path,
        'gsimlt_path': gsimlt_path,
        'sa_period': hc.sa_period,
        'sa_damping': hc.sa_damping,
        'investigation_time': hc.investigation_time,
        'imt': hc.imt,
        'imls': hc.imls,
    }


def _curve_data(hc):
    curves = models.HazardCurveData.objects.all_curves_simple(
        filter_args=dict(hazard_curve=hc.id)
    )
    # Simple object wrapper around the values, to match the interface of the
    # XML writer:
    Location = namedtuple('Location', 'x y')
    HazardCurveData = namedtuple('HazardCurveData', 'location poes')
    return (HazardCurveData(Location(x, y), poes) for x, y, poes in curves)


@core.export_output.add(('gmf_scenario', 'xml'), ('gmf', 'xml'))
def export_gmf_xml(key, output, target):
    """
    Export the GMF Collection specified by ``output`` to the ``target``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `gmf`.
    :param target:
        The same ``target`` as :func:`export`.

    :returns:
        The same return value as defined by :func:`export`.
    """
    gmf = models.Gmf.objects.get(output=output.id)
    haz_calc = output.oq_job
    if output.output_type == 'gmf':
        lt_rlz = gmf.lt_realization
        sm_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsim_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)
    else:  # gmf_scenario
        sm_lt_path = ''
        gsim_lt_path = ''
    dest = _get_result_export_dest(haz_calc.id, target, output.gmf)
    writer = hazard_writers.EventBasedGMFXMLWriter(
        dest, sm_lt_path, gsim_lt_path)
    with floatformat('%12.8E'):
        writer.serialize(gmf)
    return dest


@core.export_output.add(('ses', 'xml'))
def export_ses_xml(key, output, target):
    """
    Export the Stochastic Event Set Collection specified by ``output`` to the
    ``target``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `ses`.
    :param str target:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    ses_coll = models.SESCollection.objects.get(output=output.id)
    haz_calc = output.oq_job
    sm_lt_path = core.LT_PATH_JOIN_TOKEN.join(ses_coll.sm_lt_path)

    dest = _get_result_export_dest(haz_calc.id, target,
                                   output.ses)
    writer = hazard_writers.SESXMLWriter(dest, sm_lt_path)
    writer.serialize(ses_coll)
    return dest


@core.export_output.add(('hazard_map', 'xml'), ('hazard_map', 'geojson'))
def export_hazard_map(key, output, target):
    """
    General hazard map export code.
    """
    file_ext = key[1]
    hazard_map = models.HazardMap.objects.get(output=output)
    haz_calc = output.oq_job

    if hazard_map.lt_realization is not None:
        # If the maps are for a specified logic tree realization,
        # get the tree paths
        lt_rlz = hazard_map.lt_realization
        smlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsimlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)
    else:
        # These maps must be constructed from mean or quantile curves
        smlt_path = None
        gsimlt_path = None

    dest = _get_result_export_dest(haz_calc.id, target, output.hazard_map,
                                   file_ext=file_ext)

    metadata = {
        'quantile_value': hazard_map.quantile,
        'statistics': hazard_map.statistics,
        'smlt_path': smlt_path,
        'gsimlt_path': gsimlt_path,
        'sa_period': hazard_map.sa_period,
        'sa_damping': hazard_map.sa_damping,
        'investigation_time': hazard_map.investigation_time,
        'imt': hazard_map.imt,
        'poe': hazard_map.poe,
    }
    writer_class = (hazard_writers.HazardMapXMLWriter if file_ext == 'xml'
                    else hazard_writers.HazardMapGeoJSONWriter)
    writer = writer_class(dest, **metadata)
    writer.serialize(zip(hazard_map.lons, hazard_map.lats, hazard_map.imls))
    return dest


class _DisaggMatrix(object):
    """
    A simple data model into which disaggregation matrix information can be
    packed. The :class:`openquake.commonlib.hazard_writers.DisaggXMLWriter`
    expects a sequence of objects which match this interface.

    :param matrix:
        A n-dimensional numpy array representing a probability mass function
        produced by the disaggregation calculator. The calculator produces a 6d
        matrix, but the final results which are saved to XML are "subsets" of
        matrix showing contributions to hazard from different combinations of
        magnitude, distance, longitude, latitude, epsilon, and tectonic region
        type.
    :param dim_labels:
        Expected values are (as tuples, lists, or similar) one of the
        following, depending on the result `matrix` type:

        * ['Mag']
        * ['Dist']
        * ['TRT']
        * ['Mag', 'Dist']
        * ['Mag', 'Dist', 'Eps']
        * ['Lon', 'Lat']
        * ['Mag', 'Lon', 'Lat']
        * ['Lon', 'Lat', 'TRT']
    :param float poe:
        Probability of exceedence (specified in the calculation config file).
    :param float iml:
        Interpolated intensity value, corresponding to the ``poe``, extracted
        from the aggregated hazard curve (which was used as input to compute
        the ``matrix``).
    """

    def __init__(self, matrix, dim_labels, poe, iml):
        self.matrix = matrix
        self.dim_labels = dim_labels
        self.poe = poe
        self.iml = iml


@core.export_output.add(('disagg_matrix', 'xml'))
def export_disagg_matrix_xml(key, output, target):
    """
    Export disaggregation histograms to the ``target``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `disagg_matrix`.
    :param str target:
        Destination directory location for exported files.

    :returns:
        A list of exported file name (including the absolute path to each
        file).
    """
    # We expect 1 result per `Output`
    [disagg_result] = models.DisaggResult.objects.filter(output=output)
    lt_rlz = disagg_result.lt_realization
    haz_calc = output.oq_job

    dest = _get_result_export_dest(haz_calc.id, target,
                                   output.disagg_matrix)

    writer_kwargs = dict(
        investigation_time=disagg_result.investigation_time,
        imt=disagg_result.imt,
        lon=disagg_result.location.x,
        lat=disagg_result.location.y,
        sa_period=disagg_result.sa_period,
        sa_damping=disagg_result.sa_damping,
        mag_bin_edges=disagg_result.mag_bin_edges,
        dist_bin_edges=disagg_result.dist_bin_edges,
        lon_bin_edges=disagg_result.lon_bin_edges,
        lat_bin_edges=disagg_result.lat_bin_edges,
        eps_bin_edges=disagg_result.eps_bin_edges,
        tectonic_region_types=disagg_result.trts,
        smlt_path=core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path),
        gsimlt_path=core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path),
    )

    writer = hazard_writers.DisaggXMLWriter(dest, **writer_kwargs)

    data = (_DisaggMatrix(disagg_result.matrix[i], dim_labels,
                          disagg_result.poe, disagg_result.iml)
            for i, dim_labels in enumerate(disagg.pmf_map))

    writer.serialize(data)

    return dest


@core.export_output.add(('uh_spectra', 'xml'))
def export_uh_spectra_xml(key, output, target):
    """
    Export the specified UHS ``output`` to the ``target``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `uh_spectra`.
    :param str target:
        Destination directory location for exported files.

    :returns:
        A list containing the exported file name.
    """
    uhs = models.UHS.objects.get(output=output)
    haz_calc = output.oq_job

    dest = _get_result_export_dest(haz_calc.id, target, output.uh_spectra)

    if uhs.lt_realization is not None:
        lt_rlz = uhs.lt_realization
        smlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsimlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)
    else:
        smlt_path = None
        gsimlt_path = None

    metadata = {
        'quantile_value': uhs.quantile,
        'statistics': uhs.statistics,
        'smlt_path': smlt_path,
        'gsimlt_path': gsimlt_path,
        'poe': uhs.poe,
        'periods': uhs.periods,
        'investigation_time': uhs.investigation_time,
    }

    writer = hazard_writers.UHSXMLWriter(dest, **metadata)
    writer.serialize(uhs)

    return dest
