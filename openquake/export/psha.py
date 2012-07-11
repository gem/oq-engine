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


"""Functions that export PSHA results from the OpenQuake db to NRML."""


import os

from openquake.db import models

from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.output import hazard as hzrd_out


LOG = logs.LOG


def export_psha(output, target_dir):
    """Export the specified ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` associated with PSHA calculation
        results.
    :param str target_dir:
        Destination directory location of the exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    assert output.output_type in ("hazard_curve", "hazard_map"), (
        "wrong output type, should either be a hazard curve or a map")

    path = os.path.join(target_dir, output.display_name)
    if output.output_type == "hazard_curve":
        [dba] = models.HazardCurve.objects.filter(output=output)
    else:
        [dba] = models.HazardMap.objects.filter(output=output)


def nrml_path(job_ctxt, rtype, datum=None):
    """Return meta data required for hazard curve serialization.

    :param job_ctxt: the `JobContext` instance to use.
    :param str rtype: hazard curve type, one of: curve, mean, quantile
    :param datum: one of: realization, None, quantile
    :returns: a 3-tuple with the kvs key template, the nrml path and a dict
        containing serialization meta data respectively.
    """
    if rtype == "curve":
        result = job_ctxt.build_nrml_path("hazardcurve-%s.xml" % datum)
    elif rtype == "mean":
        result = job_ctxt.build_nrml_path("hazardcurve-mean.xml")
    elif rtype == "quantile":
        result = job_ctxt.build_nrml_path(
            "hazardcurve-quantile-%.2f.xml" % datum)
    else:
        raise ValueError("Unknown curve type: '%s'" % rtype)

    return result


def hcs_meta(job_ctxt, rtype, datum=None):
    """Return meta data required for hazard curve serialization.

    :param job_ctxt: the `JobContext` instance to use.
    :param str rtype: hazard curve type, one of: curve, mean, quantile
    :param datum: one of: realization, None, quantile
    :returns: a 3-tuple with the kvs key template, the nrml path and a dict
        containing serialization meta data respectively.
    """
    if rtype == "curve":
        key_template = kvs.tokens.hazard_curve_poes_key_template(
            job_ctxt.job_id, datum)
        hc_meta = {"endBranchLabel": datum}
    elif rtype == "mean":
        key_template = kvs.tokens.mean_hazard_curve_key_template(
            job_ctxt.job_id)
        hc_meta = {"statistics": "mean"}
    elif rtype == "quantile":
        key_template = kvs.tokens.quantile_hazard_curve_key_template(
            job_ctxt.job_id, str(datum))
        hc_meta = {"statistics": "quantile", "quantileValue": datum}
    else:
        raise ValueError("Unknown curve type: '%s'" % rtype)

    return (key_template, nrml_path(job_ctxt, rtype, datum), hc_meta)


def hms_meta(job_ctxt, rtype, data):
    """Return meta data required for hazard map serialization.

    :param job_ctxt: the `JobContext` instance to use.
    :param str rtype: result type, one of: mean, quantile
    :param data: a tuple containing just the poe or the poe and the quantile
    :returns: a 3-tuple with the kvs key template, the nrml path and a dict
        containing serialization meta data respectively.
    """
    if rtype == "mean":
        file_name = "hazardmap-%s-mean.xml" % data[0]
        hm_meta = {"statistics": "mean"}
        key_template = kvs.tokens.mean_hazard_map_key_template(
            job_ctxt.job_id, data[0])
    elif rtype == "quantile":
        file_name = "hazardmap-%s-quantile-%.2f.xml" % data
        hm_meta = {"statistics": "quantile", "quantileValue": data[1]}
        key_template = kvs.tokens.quantile_hazard_map_key_template(
            job_ctxt.job_id, *data)
    else:
        raise ValueError("Unknown map type: '%s'" % rtype)

    return (key_template, job_ctxt.build_nrml_path(file_name), hm_meta)


def map2db(job_ctxt, sites, poes, quantile=None):
    """Write (mean|quantile) hazard map data to database.

    :param job_ctxt: the `JobContext` instance to use.
    :param sites: the sites for which the maps will be serialized
    :type sites: list of :py:class:`openquake.shapes.Site`
    :param poes: the PoEs at which the maps will be serialized
    :type poes: list of :py:class:`float`
    :param float quantile: the quantile at which the maps will be serialized
    """
    rtype = "mean" if quantile is None else "quantile"
    for poe in poes:
        datum = (poe,) if quantile is None else (poe, quantile)
        key_template, path, hm_meta = hms_meta(job_ctxt, rtype, datum)

        LOG.info("Generating hazard map file for PoE %s, "
                 "%s nodes" % (poe, len(sites)))

        map_writer = hzrd_out.HazardMapDBWriter(path, job_ctxt.job_id)
        hm_data = []

        for site in sites:
            key = key_template % hash(site)
            # use hazard map IML values from KVS
            hm_attrib = {
                'investigationTimeSpan': job_ctxt['INVESTIGATION_TIME'],
                'IMT': job_ctxt['INTENSITY_MEASURE_TYPE'],
                'vs30': job_ctxt['REFERENCE_VS30_VALUE'],
                'IML': kvs.get_value_json_decoded(key),
                'poE': poe}

            hm_attrib.update(hm_meta)
            hm_data.append((site, hm_attrib))

        LOG.debug(">> path: %s" % path)
        map_writer.serialize(hm_data)


def check_target_dir(path):
    """Make sure the NRML output directory exists.

    :param str path: full NRML output file path
    """
    LOG.debug("> check_target_dir")
    target_dir = os.path.dirname(path)
    if os.path.exists(target_dir):
        if not os.path.isdir(target_dir):
            # If it's not a directory, we can't do anything.
            # This is a problem
            raise RuntimeError('%s already exists and is not a directory.'
                               % target_dir)
    else:
        os.makedirs(target_dir)
    LOG.debug("< check_target_dir")


def curves2nrml(job_ctxt):
    """Write hazard curves to NRML files.

    :param job_ctxt: the `JobContext` instance to use.
    """
    LOG.debug("> curves2nrml")
    hcs = models.HazardCurve.objects.filter(output__oq_job=job_ctxt.job_id,
                                            output__output_type="hazard_curve")

    for hc in hcs:
        curve2nrml(job_ctxt, hc)
    LOG.debug("< curves2nrml")


def curve2nrml(job_ctxt, hc, path_to_use=None):
    """Write a single hazard curve to a NRML file.

    :param job_ctxt: the `JobContext` instance to use.
    :param hc: the :py:class:`openquake.db.models.HazardCurve` instance to dump
    :param str path_to_use: optional path to use for serialization
    """
    LOG.debug("> curve2nrml")
    rtype = hc.statistic_type if hc.statistic_type is not None else "curve"
    datum = hc.end_branch_label if rtype == "curve" else hc.quantile

    _, path, hc_meta = hcs_meta(job_ctxt, rtype, datum)

    if path_to_use:
        path = path_to_use
    LOG.debug("*> path: '%s'" % path)
    check_target_dir(path)

    writer = hzrd_out.HazardCurveXMLWriter(path)
    hc_data = []
    db_data = hc.hazardcurvedata_set.all()
    for hcd in db_data:
        hc_attrib = {
            "investigationTimeSpan": job_ctxt["INVESTIGATION_TIME"],
            "IMLValues": job_ctxt.imls,
            "IMT": job_ctxt["INTENSITY_MEASURE_TYPE"],
            "PoEValues": hcd.poes}
        hc_attrib.update(hc_meta)
        site = shapes.Site(longitude=hcd.location.x, latitude=hcd.location.y)
        hc_data.append((site, hc_attrib))

    writer.serialize(hc_data)
    LOG.debug("< curve2nrml")
    return path


def maps2nrml(job_ctxt, poes, quantiles):
    """Write hazard maps to NRML files.

    :param job_ctxt: the `JobContext` instance to use.
    :param poes: the PoEs at which the maps will be serialized
    :type poes: list of :py:class:`float`
    :param quantiles: the quantile to be serialized
    :type quantiles: a list of :py:class:`float`
    """
    LOG.debug("> maps2nrml")
    for poe in poes:
        _, path, hm_meta = hms_meta(job_ctxt, "mean", (poe,))
        map2nrml(job_ctxt, path, hm_meta)

    for quantile in quantiles:
        for poe in poes:
            _, path, hm_meta = hms_meta(job_ctxt, "quantile", (poe, quantile))
            map2nrml(job_ctxt, path, hm_meta)
    LOG.debug("< maps2nrml")


def map2nrml(job_ctxt, path, hm_meta):
    """Write a single hazard map to a NRML file.

    :param job_ctxt: the `JobContext` instance to use.
    :param str path: the NRML path for the hazard map at hand
    :param dict hm_meta: hazard map serialization meta data
    """
    LOG.debug("> map2nrml")
    [hm] = models.HazardMap.objects.filter(
        output__oq_job=job_ctxt.job_id, output__output_type="hazard_map",
        output__display_name=os.path.basename(path))

    LOG.debug("*> path: '%s'" % path)
    check_target_dir(path)

    writer = hzrd_out.HazardMapXMLWriter(path)
    hm_data = []
    db_data = hm.hazardmapdata_set.all()
    for hmd in db_data:
        hm_attrib = {
            "investigationTimeSpan": job_ctxt["INVESTIGATION_TIME"],
            "IMT": job_ctxt["INTENSITY_MEASURE_TYPE"],
            "vs30": job_ctxt["REFERENCE_VS30_VALUE"],
            "IML": hmd.value,
            "poE": hm.poe}
        hm_attrib.update(hm_meta)
        site = shapes.Site(longitude=hmd.location.x, latitude=hmd.location.y)
        hm_data.append((site, hm_attrib))

    writer.serialize(hm_data)
    LOG.debug("< map2nrml")
