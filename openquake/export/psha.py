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


"""Functions that export PSHA results from the OpenQuake db to NRML."""


from openquake import kvs
from openquake import logs


LOG = logs.LOG


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
