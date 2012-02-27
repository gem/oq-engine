# Copyright (c) 2010-2012, GEM Foundation.
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


"""Functions for getting information about completed calculations and
calculation outputs, as well as exporting outputs from the database to various
file formats."""


from openquake.db import models


def _export_fn_map():
    """Creates a mapping from output type to export function.

    :rtype: `dict`
    """
    # TODO: No export functions have yet been written.
    fn_map = {}
    return fn_map


def _export_fn_not_implemented(output, _target_dir):
    """This gets called if an export is attempted on an unsupported output
    type. See :data:`_EXPORT_FN_MAP`."""
    raise NotImplementedError('Cannot export output of type: %s'
                              % output.output_type)


def get_calculations(user_name):
    """Get the completed calculations (successful and failed) for the given
    user_name.

    Results are given in reverse chronological order.

    :param str user_name:
        Owner of the returned results.
    :returns:
        :class:`django.db.models.query.QuerySet` of
        :class:`openquake.db.models.OqCalculation` objects, sorted in
        reverse chronological order.
    :rtype:
        :class:`django.db.models.query.QuerySet`
    """
    return models.OqCalculation.objects.filter(
        owner__user_name=user_name).extra(
            where=["status in ('succeeded', 'failed')"]).order_by(
                '-last_update')


def get_outputs(calculation_id):
    """Get all :class:`openquake.db.models.Output`s associated with the
    specified calculation.

    :param int calculation_id:
        ID of a :class:`openquake.db.models.OqCalculation`.
    :returns:
        :class:`django.db.models.query.QuerySet` of
        :class:`openquake.db.models.Output` objects.
    """
    return models.Output.objects.filter(oq_calculation=calculation_id)


def export(output_id, target_dir):
    """Export the given calculation output from the database to the specified
    directory.

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
        output.output_type, _export_fn_not_implemented)

    return export_fn(output, target_dir)
