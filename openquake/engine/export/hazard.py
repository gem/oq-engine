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

"""
Functionality for exporting and serializing hazard curve calculation results.
"""


import os

from collections import namedtuple
from collections import OrderedDict

from openquake.hazardlib.calc import disagg
from openquake.nrmllib.hazard import writers

from openquake.engine.db import models
from openquake.engine.export import core


# for each output_type there must be a function
# export_<output_type>(output, target)
def export(output_id, target, export_type='xml'):
    """
    Export the given hazard calculation output from the database to the
    specified directory.

    :param int output_id:
        ID of a :class:`openquake.engine.db.models.Output`.
    :param target:
        Output directory OR a file-like object to write results to.
    :param export_type:
        The desired export format. Defaults to 'xml'.
    :returns:
        Return the complete file path OR the file-like object itself where the
        results were written to, depending on what ``target`` is.
    """
    output = models.Output.objects.get(id=output_id)

    try:
        export_fn = EXPORTERS[export_type][output.output_type]
    except KeyError:
        raise NotImplementedError(
            'No "%(fmt)s" exporter is available for "%(output_type)s"'
            ' outputs' % dict(fmt=export_type, output_type=output.output_type)
        )

    # If the `target` is a string directory path, use expand user to handle
    # tokens like '~':
    if isinstance(target, (basestring, buffer)):
        target = os.path.expanduser(target)
    return export_fn(output, target)


def _get_result_export_dest(calc_id, target, result, file_ext='xml'):
    """
    Get the full absolute path (including file name) for a given ``result``.

    As a side effect, intermediate directories are created such that the file
    can be created and written to immediately.

    :param int calc_id:
        ID of the associated
        :class:`openquake.engine.db.models.HazardCalculation`.
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
    if output_type == 'complete_lt_gmf':
        type_dir = 'gmf'
    elif output_type == 'complete_lt_ses':
        type_dir = 'ses'

    imt_dir = ''  # if blank, we don't have an IMT dir
    if output_type in ('hazard_curve', 'hazard_map', 'disagg_matrix'):
        imt_dir = result.imt
        if result.imt == 'SA':
            imt_dir = 'SA-%s' % result.sa_period

    # construct the directory which will contain the result XML file:
    directory = os.path.join(target, calc_dir, type_dir, imt_dir)
    core.makedirs(directory)

    if output_type in ('hazard_curve', 'hazard_map', 'uh_spectra'):
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
    elif output_type in ('gmf', 'ses'):
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
    elif output_type == 'disagg_matrix':
        # only logic trees, no stats
        location = 'lon_%s-lat_%s' % (result.location.x, result.location.y)

        ltr = result.lt_realization
        sm_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.sm_lt_path)
        gsim_ltp = core.LT_PATH_JOIN_TOKEN.join(ltr.gsim_lt_path)
        if ltr.weight is None:
            # Monte-Carlo logic tree sampling
            filename = '%s-%s-smltp_%s-gsimltp_%s-ltr_%s.%s' % (
                output_type, location, sm_ltp, gsim_ltp, ltr.ordinal, file_ext
            )
        else:
            # End Branch Enumeration
            filename = '%s-%s-smltp_%s-gsimltp_%s.%s' % (
                output_type, location, sm_ltp, gsim_ltp, file_ext
            )
    else:
        filename = '%s.%s' % (output_type, file_ext)

    return os.path.abspath(os.path.join(directory, filename))


@core.makedirsdeco
def export_hazard_curve_xml(output, target):
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
    hc = models.HazardCurve.objects.get(output=output.id)

    hcd = _curve_data(hc)
    metadata, dest = _curve_metadata(output, target)
    writers.HazardCurveXMLWriter(dest, **metadata).serialize(hcd)

    return dest


@core.makedirsdeco
def export_hazard_curve_multi_xml(output, target):
    hcs = output.hazard_curve

    data = [_curve_data(hc) for hc in hcs]

    metadata_set = []
    for hc in hcs:
        metadata, dest = _curve_metadata(hc.output, target)
        metadata_set.append(metadata)
    assert(dest is not None)

    writer = writers.MultiHazardCurveXMLWriter(dest, metadata_set)
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

    haz_calc = output.oq_job.hazard_calculation
    dest = _get_result_export_dest(
        haz_calc.id, target, output.hazard_curve)

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
    }, dest


def _curve_data(hc):
    curves = models.HazardCurveData.objects.all_curves_simple(
        filter_args=dict(hazard_curve=hc.id)
    )
    # Simple object wrapper around the values, to match the interface of the
    # XML writer:
    Location = namedtuple('Location', 'x y')
    HazardCurveData = namedtuple('HazardCurveData', 'location poes')
    return (HazardCurveData(Location(x, y), poes) for x, y, poes in curves)


@core.makedirsdeco
def export_gmf_xml(output, target):
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
    gmf_coll = models.Gmf.objects.get(output=output.id)
    lt_rlz = gmf_coll.lt_realization
    haz_calc = output.oq_job.hazard_calculation

    if output.output_type == 'complete_lt_gmf':
        sm_lt_path = None
        gsim_lt_path = None
    else:
        sm_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsim_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

    dest = _get_result_export_dest(haz_calc.id, target, output.gmf)

    writer = writers.EventBasedGMFXMLWriter(
        dest, sm_lt_path, gsim_lt_path)
    writer.serialize(gmf_coll)

    return dest

export_complete_lt_gmf_xml = export_gmf_xml


@core.makedirsdeco
def export_gmf_scenario_xml(output, target):
    """
    Export the GMFs specified by ``output`` to the ``target``.

    :param output:
        :class:`openquake.engine.db.models.Output`
        with an `output_type` of `gmf_scenario`.
    :param target:
        The same ``target`` as :func:`export`.

    :returns:
        The same return value as defined by :func:`export`.
    """
    haz_calc = output.oq_job.hazard_calculation
    dest = _get_result_export_dest(haz_calc.id, target, output.gmf)
    gmfs = models.get_gmfs_scenario(output)
    writer = writers.ScenarioGMFXMLWriter(dest)
    writer.serialize(gmfs)
    return dest


@core.makedirsdeco
def export_ses_xml(output, target):
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
    haz_calc = output.oq_job.hazard_calculation

    if output.output_type == 'complete_lt_ses':
        sm_lt_path = None
        gsim_lt_path = None
    else:
        lt_rlz = ses_coll.lt_realization
        sm_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsim_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

    dest = _get_result_export_dest(haz_calc.id, target,
                                   output.ses)

    writer = writers.SESXMLWriter(dest, sm_lt_path, gsim_lt_path)
    writer.serialize(ses_coll)

    return dest

export_complete_lt_ses_xml = export_ses_xml


def _export_hazard_map(output, target, writer_class, file_ext):
    """
    General hazard map export code.
    """
    hazard_map = models.HazardMap.objects.get(output=output)
    haz_calc = output.oq_job.hazard_calculation

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

    writer = writer_class(dest, **metadata)
    writer.serialize(zip(hazard_map.lons, hazard_map.lats, hazard_map.imls))
    return dest


def export_hazard_map_xml(output, target):
    """
    Export the specified hazard map ``output`` to the ``target`` as
    NRML/XML.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `hazard_map`.
    :param target:
        Destination directory location for exported files.

    :returns:
        A list of exported file name (including the absolute path to each
        file).
    """
    return _export_hazard_map(output, target, writers.HazardMapXMLWriter,
                              'xml')


def export_hazard_map_geojson(output, target):
    """
    The same thing as :func:`export_hazard_map_xml`, except results are saved
    in GeoJSON format.
    """
    return _export_hazard_map(output, target,
                              writers.HazardMapGeoJSONWriter, 'geojson')


class _DisaggMatrix(object):
    """
    A simple data model into which disaggregation matrix information can be
    packed. The :class:`openquake.nrmllib.hazard.writers.DisaggXMLWriter`
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


@core.makedirsdeco
def export_disagg_matrix_xml(output, target):
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
    haz_calc = output.oq_job.hazard_calculation

    dest = _get_result_export_dest(haz_calc.id, target,
                                   output.disagg_matrix)

    pmf_map = OrderedDict([
        (('Mag', ), disagg.mag_pmf),
        (('Dist', ), disagg.dist_pmf),
        (('TRT', ), disagg.trt_pmf),
        (('Mag', 'Dist'), disagg.mag_dist_pmf),
        (('Mag', 'Dist', 'Eps'), disagg.mag_dist_eps_pmf),
        (('Lon', 'Lat'), disagg.lon_lat_pmf),
        (('Mag', 'Lon', 'Lat'), disagg.mag_lon_lat_pmf),
        (('Lon', 'Lat', 'TRT'), disagg.lon_lat_trt_pmf),
    ])

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

    writer = writers.DisaggXMLWriter(dest, **writer_kwargs)

    data = (_DisaggMatrix(pmf_fn(disagg_result.matrix), dim_labels,
                          disagg_result.poe, disagg_result.iml)
            for dim_labels, pmf_fn in pmf_map.iteritems())

    writer.serialize(data)

    return dest


@core.makedirsdeco
def export_uh_spectra_xml(output, target):
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
    haz_calc = output.oq_job.hazard_calculation

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

    writer = writers.UHSXMLWriter(dest, **metadata)
    writer.serialize(uhs)

    return dest


XML_EXPORTERS = {
    'complete_lt_gmf': export_complete_lt_gmf_xml,
    'complete_lt_ses': export_complete_lt_ses_xml,
    'disagg_matrix': export_disagg_matrix_xml,
    'gmf': export_gmf_xml,
    'gmf_scenario': export_gmf_scenario_xml,
    'hazard_curve': export_hazard_curve_xml,
    'hazard_curve_multi': export_hazard_curve_multi_xml,
    'hazard_map': export_hazard_map_xml,
    'ses': export_ses_xml,
    'uh_spectra': export_uh_spectra_xml,
}
GEOJSON_EXPORTERS = {
    'hazard_map': export_hazard_map_geojson,
}
EXPORTERS = {
    'xml': XML_EXPORTERS,
    'geojson': GEOJSON_EXPORTERS,
}
