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
from openquake import nrmllib
from openquake.nrmllib import writers

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.export import core
from openquake.engine.input import logictree


LOG = logs.LOG


# for each output_type there must be a function
# export_<output_type>(output, target_dir)
def export(output_id, target_dir, check_schema=False):
    """
    Export the given hazard calculation output from the database to the
    specified directory.

    :param int output_id:
        ID of a :class:`openquake.engine.db.models.Output`.
    :param str target_dir:
        Directory where output artifacts should be written.
    :param bool check_schema:
        If True, checks that the generated file is valid for the NRML schema
    :returns:
        List of file names (including the full directory path) containing the
        exported results.

        The quantity and type of the result files depends on
        the type of output, as well as calculation parameters. (See the
        `output_type` attribute of :class:`openquake.engine.db.models.Output`.)
    """
    output = models.Output.objects.get(id=output_id)
    export_fn = globals().get(
        'export_' + output.output_type, core._export_fn_not_implemented)
    fnames = export_fn(output, os.path.expanduser(target_dir))
    if check_schema:
        for fname in fnames:
            nrmllib.assert_valid(fname)
    return fnames


HAZARD_CURVES_FILENAME_FMT = 'hazard-curves-%(hazard_curve_id)s.xml'
HAZARD_MAP_FILENAME_FMT = 'hazard-map-%(hazard_map_id)s.xml'
GMF_FILENAME_FMT = 'gmf-%(gmf_coll_id)s.xml'
SES_FILENAME_FMT = 'ses-%(ses_coll_id)s.xml'
COMPLETE_LT_SES_FILENAME_FMT = 'complete-lt-ses-%(ses_coll_id)s.xml'
COMPLETE_LT_GMF_FILENAME_FMT = 'complete-lt-gmf-%(gmf_coll_id)s.xml'
GMF_SCENARIO_FMT = 'gmf-%(output_id)s.xml'


def _get_end_branch_export_path(target_dir, result, ltp):
    """
    Given a hazard result for a particular logic tree end branch, construct an
    export path by concatenating ``target_dir``, GSIM name, and IMT, create the
    directory structure (if it doesn't already exist), and return the path.

    In the resulting path, the IMT is used as-is, except for SA IMTs. In this
    case, the IMT component of the path is formatted like so:

    `SA[0025]` for SA with a period of 0.025.

    :param str target_dir:
        Destination directory location for exported files.
    :param result:
        :mod:`openquake.engine.db.models` result object `with a foreign key
        reference to :class:`~openquake.engine.db.models.LtRealization`. The
        realization is needed to identify the logic tree paths, and thus, the
        name of the GSIM.

        ``result`` should also have the following the attributes:

        * imt
        * sa_period

        See :class:`~openquake.engine.db.models.HazardCurve` for an example.
    :param ltp:
        Instance of a :class:`~openquake.engine.input.logictree.\
LogicTreeProcessor`.
    """
    lt_rlz = result.lt_realization
    gsim_dir_name = '_'.join(
        [ltp.gmpe_lt.branches[br].value.__class__.__name__
         for br in lt_rlz.gsim_lt_path]
    )

    imt = result.imt
    if imt == 'SA':
        # if it's SA, include the period
        period = str(result.sa_period)
        period = period.replace('.', '')
        imt = 'SA[%s]' % period

    export_dir = os.path.abspath(os.path.join(target_dir, gsim_dir_name, imt))
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    return export_dir


@core.makedirs
def export_hazard_curve(output, target_dir):
    """
    Export the specified hazard curve ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `hazard_curve`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    hc = models.HazardCurve.objects.get(output=output.id)

    curves = models.HazardCurveData.objects.all_curves_simple(
        filter_args=dict(hazard_curve=hc.id)
    )
    # Simple object wrapper around the values, to match the interface of the
    # XML writer:
    Location = namedtuple('Location', 'x y')
    HazardCurveData = namedtuple('HazardCurveData', 'location poes')
    hcd = (HazardCurveData(Location(x, y), poes) for x, y, poes in curves)

    filename = HAZARD_CURVES_FILENAME_FMT % dict(hazard_curve_id=hc.id)

    if hc.lt_realization is not None:
        # If the curves are for a specified logic tree realization,
        # get the tree paths
        lt_rlz = hc.lt_realization
        smlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsimlt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

        # Also include the GSIM name and IMT in the directory structure.
        # This is much more useful and organized than simply dumping all of the
        # results to a single directory.
        haz_calc = hc.lt_realization.hazard_calculation
        ltp = logictree.LogicTreeProcessor(haz_calc.id)
        export_dir = _get_end_branch_export_path(target_dir, hc, ltp)
        path = os.path.join(export_dir, filename)
    else:
        # These curves must be statistical aggregates
        smlt_path = None
        gsimlt_path = None
        path = os.path.abspath(os.path.join(target_dir, filename))

    metadata = {
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
    writer = writers.HazardCurveXMLWriter(path, **metadata)
    writer.serialize(hcd)

    return [path]


@core.makedirs
def export_gmf(output, target_dir):
    """
    Export the GMF Collection specified by ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `gmf`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    gmf_coll = models.GmfCollection.objects.get(output=output.id)
    lt_rlz = gmf_coll.lt_realization

    if output.output_type == 'complete_lt_gmf':
        filename = COMPLETE_LT_GMF_FILENAME_FMT % dict(gmf_coll_id=gmf_coll.id)

        # For the `complete logic tree` GMF, the LT paths are not relevant.
        sm_lt_path = None
        gsim_lt_path = None
    else:
        # output type should be `gmf`
        filename = GMF_FILENAME_FMT % dict(gmf_coll_id=gmf_coll.id)

        sm_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsim_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

    path = os.path.abspath(os.path.join(target_dir, filename))

    writer = writers.EventBasedGMFXMLWriter(
        path, sm_lt_path, gsim_lt_path)
    writer.serialize(gmf_coll)

    return [path]

export_complete_lt_gmf = export_gmf


@core.makedirs
def export_gmf_scenario(output, target_dir):
    """
    Export the GMFs specified by ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output`
        with an `output_type` of `gmf_scenario`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    gmfs = models.get_gmfs_scenario(output)
    filename = GMF_SCENARIO_FMT % dict(output_id=output.id)
    path = os.path.abspath(os.path.join(target_dir, filename))
    writer = writers.ScenarioGMFXMLWriter(path)
    writer.serialize(gmfs)
    return [path]


@core.makedirs
def export_ses(output, target_dir):
    """
    Export the Stochastic Event Set Collection specified by ``output`` to the
    ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `ses`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    ses_coll = models.SESCollection.objects.get(output=output.id)
    # lt_rlz can be `None` in the case of a `complete logic tree` SES
    lt_rlz = ses_coll.lt_realization

    if output.output_type == 'complete_lt_ses':
        filename = COMPLETE_LT_SES_FILENAME_FMT % dict(ses_coll_id=ses_coll.id)

        # For the `complete logic tree` SES, the LT paths are not relevant.
        sm_lt_path = None
        gsim_lt_path = None
    else:
        # output_type should be `ses`
        filename = SES_FILENAME_FMT % dict(ses_coll_id=ses_coll.id)

        sm_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsim_lt_path = core.LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

    path = os.path.abspath(os.path.join(target_dir, filename))

    writer = writers.SESXMLWriter(path, sm_lt_path, gsim_lt_path)
    writer.serialize(ses_coll)

    return [path]

export_complete_lt_ses = export_ses


@core.makedirs
def export_hazard_map(output, target_dir):
    """
    Export the specified hazard map ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `hazard_map`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file name (including the absolute path to each
        file).
    """
    hazard_map = models.HazardMap.objects.get(output=output)

    filename = HAZARD_MAP_FILENAME_FMT % dict(hazard_map_id=hazard_map.id)
    path = os.path.abspath(os.path.join(target_dir, filename))

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

    writer = writers.HazardMapXMLWriter(path, **metadata)
    writer.serialize(zip(hazard_map.lons, hazard_map.lats, hazard_map.imls))
    return [path]


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


@core.makedirs
def export_disagg_matrix(output, target_dir):
    """
    Export disaggregation histograms to the ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `disagg_matrix`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file name (including the absolute path to each
        file).
    """
    # We expect 1 result per `Output`
    [disagg_result] = models.DisaggResult.objects.filter(output=output)
    lt_rlz = disagg_result.lt_realization

    filename = '%s.xml' % output.display_name
    haz_calc = disagg_result.lt_realization.hazard_calculation
    ltp = logictree.LogicTreeProcessor(haz_calc.id)
    export_dir = _get_end_branch_export_path(target_dir, disagg_result, ltp)
    path = os.path.abspath(os.path.join(export_dir, filename))

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

    writer = writers.DisaggXMLWriter(path, **writer_kwargs)

    data = (_DisaggMatrix(pmf_fn(disagg_result.matrix), dim_labels,
                          disagg_result.poe, disagg_result.iml)
            for dim_labels, pmf_fn in pmf_map.iteritems())

    writer.serialize(data)

    return [path]


@core.makedirs
def export_uh_spectra(output, target_dir):
    """
    Export the specified UHS ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.engine.db.models.Output` with an `output_type` of
        `uh_spectra`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list containing the exported file name.
    """
    uhs = models.UHS.objects.get(output=output)

    filename = '%s.xml' % output.display_name
    path = os.path.abspath(os.path.join(target_dir, filename))

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
    }

    writer = writers.UHSXMLWriter(path, **metadata)
    writer.serialize(uhs)

    return [path]
