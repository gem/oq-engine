# Copyright (c) 2010-2012, GEM Foundation.
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

from nrml import writers as nrml_writers

from openquake import logs
from openquake.db import models
from openquake.export import core
from openquake.export import uhs
from openquake.export.core import makedirs


LOG = logs.LOG


def export(output_id, target_dir):
    """
    Export the given hazard calculation output from the database to the
    specified directory.

    :param int output_id:
        ID of a :class:`openquake.db.models.Output`.
    :param str target_dir:
        Directory where output artifacts should be written.
    :returns:
        List of file names (including the full directory path) containing the
        exported results.

        The quantity and type of the result files depends on
        the type of output, as well as calculation parameters. (See the
        `output_type` attribute of :class:`openquake.db.models.Output`.)
    """
    output = models.Output.objects.get(id=output_id)

    export_fn = _export_fn_map().get(
        output.output_type, core._export_fn_not_implemented)

    return export_fn(output, os.path.expanduser(target_dir))


def _export_fn_map():
    """
    Creates a mapping from output type to export function.

    Each export function should implement a common interface and accept two
    arguments: a :class:`~openquake.db.models.Output` object and a target
    dir (`str`).

    Each function should return a list of the file names created by the export
    action.
    """

    fn_map = {
        'uh_spectra': uhs.export_uhs,
        'hazard_curve': export_hazard_curves,
        'gmf': export_gmf,
        'ses': export_ses,
        'complete_lt_ses': export_ses,
    }
    return fn_map


HAZARD_CURVES_FILENAME_FMT = 'hazard-curves-%(hazard_curve_id)s.xml'
GMF_FILENAME_FMT = 'gmf-%(gmf_coll_id)s.xml'
SES_FILENAME_FMT = 'ses-%(ses_coll_id)s.xml'
#: Used to separate node labels in a logic tree path
LT_PATH_JOIN_TOKEN = '|'


@makedirs
def export_hazard_curves(output, target_dir):
    """
    Export the specified hazard curve ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` with an `output_type` of
        `hazard_curve`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    hc = models.HazardCurve.objects.get(output=output.id)
    hcd = models.HazardCurveData.objects.filter(hazard_curve=hc.id)

    filename = HAZARD_CURVES_FILENAME_FMT % dict(hazard_curve_id=hc.id)
    path = os.path.abspath(os.path.join(target_dir, filename))

    if hc.lt_realization is not None:
        # If the curves are for a specified logic tree realization,
        # get the tree paths
        lt_rlz = hc.lt_realization
        smlt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsimlt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)
    else:
        # These curves must be statistical aggregates
        smlt_path = None
        gsimlt_path = None

    metadata = {
        'quantile_value': hc.quantile,
        'statistics': hc.statistics,
        'smlt_path': smlt_path,
        'gsimlt_path': gsimlt_path,
        'sa_period': hc.sa_period,
        'sa_damping': hc.sa_damping,
    }
    writer = nrml_writers.HazardCurveXMLWriter(
        path, hc.investigation_time, hc.imt, hc.imls, **metadata)
    writer.serialize(hcd)

    return [path]


# TODO(LB): We may need to differentiate between GMFs calculated by the
# Event-Based calculator and the Scenario calculator. At the moment, this
# exporter is intended for Event-Based GMF results. The structures for the two
# result types are slightly different.
@makedirs
def export_gmf(output, target_dir):
    """
    Export the GMF Collection specified by ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` with an `output_type` of `gmf`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    gmf_coll = models.GmfCollection.objects.get(output=output.id)
    lt_rlz = gmf_coll.lt_realization
    sm_lt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
    gsim_lt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

    filename = GMF_FILENAME_FMT % dict(gmf_coll_id=gmf_coll.id)
    path = os.path.abspath(os.path.join(target_dir, filename))

    writer = nrml_writers.EventBasedGMFXMLWriter(
        path, sm_lt_path, gsim_lt_path)
    writer.serialize(gmf_coll)

    return [path]


@makedirs
def export_ses(output, target_dir):
    """
    Export the Stochastic Event Set Collection specified by ``output`` to the
    ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` with an `output_type` of `ses`.
    :param str target_dir:
        Destination directory location for exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    ses_coll = models.SESCollection.objects.get(output=output.id)
    lt_rlz = ses_coll.lt_realization
    # The tree paths can be `None`, in the case of `complete logic tree` SES
    sm_lt_path = None
    gsim_lt_path = None
    if lt_rlz is not None:
        sm_lt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.sm_lt_path)
        gsim_lt_path = LT_PATH_JOIN_TOKEN.join(lt_rlz.gsim_lt_path)

    filename = SES_FILENAME_FMT % dict(ses_coll_id=ses_coll.id)
    path = os.path.abspath(os.path.join(target_dir, filename))

    writer = nrml_writers.SESXMLWriter(path, sm_lt_path, gsim_lt_path)
    writer.serialize(ses_coll)

    return [path]


def curves2nrml(target_dir, job):
    """Write hazard curves to NRML files.

    :param str target_dir: where should the output files go?
    :param int job_id: the database key of the job at hand.
    """
    LOG.debug("> curves2nrml")
    hc_outputs = models.Output.objects.filter(oq_job=job,
                                              output_type="hazard_curve")

    for hc_output in hc_outputs:
        export_hazard_curves(hc_output, target_dir)

    hco_count = len(hc_outputs)
    if hco_count > 1:
        logs.log_progress(
            "%s hazard curves exported to %s" % (hco_count, target_dir), 2)
    elif hco_count == 1:
        logs.log_progress("One hazard curve exported to %s" % target_dir, 2)
    else:
        logs.log_progress("No hazard curves found for export", 2)

    LOG.debug("< curves2nrml")
