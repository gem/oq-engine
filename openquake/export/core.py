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

"""Functions for getting information about completed jobs and
calculation outputs, as well as exporting outputs from the database to various
file formats."""


import os

from openquake.db import models


def _export_fn_map():
    """Creates a mapping from output type to export function.

    The specific export functions should accept two parameters: a
    :class:`openquake.db.models.Output` object and a taret dir (`str`).

    Each function should return a list of the file names created by the export
    action.

    :rtype: `dict`
    """
    # Silencing `Reimport <module>` warnings
    # pylint: disable=W0404
    from openquake.export import uhs
    from openquake.export import risk

    fn_map = {
        'dmg_dist_per_asset': risk.export_dmg_dist_per_asset,
        'dmg_dist_per_taxonomy': risk.export_dmg_dist_per_taxonomy,
        'collapse_map': risk.export_collapse_map,
        'dmg_dist_total': risk.export_dmg_dist_total,
        'uh_spectra': uhs.export_uhs,
        'agg_loss_curve': risk.export_agg_loss_curve,
    }
    return fn_map


def _export_fn_not_implemented(output, _target_dir):
    """This gets called if an export is attempted on an unsupported output
    type. See :data:`_EXPORT_FN_MAP`."""
    raise NotImplementedError('Cannot export output of type: %s'
                              % output.output_type)


def makedirs(fn):
    """Decorator for export functions. Creates intermediate directories (if
    necessary) to the target export directory.

    This is equivalent to `mkdir -p` and :function:`os.makedirs`.
    """

    def wrapped(output, target_dir):
        """Call :function:`os.makedirs` to create intermediate directories to
        the ``target_dir``.
        """
        if os.path.exists(target_dir):
            if not os.path.isdir(target_dir):
                # If it's not a directory, we can't do anything.
                # This is a problem
                raise RuntimeError('%s already exists and is not a directory.'
                                   % target_dir)
        else:
            os.makedirs(target_dir)
        return fn(output, target_dir)

    # This fixes doc generation problems with decorators
    wrapped.__doc__ = fn.__doc__
    wrapped.__repr__ = fn.__repr__

    return wrapped


def get_jobs(user_name):
    """Get the completed jobs (successful and failed) for the given user_name.

    Results are given in reverse chronological order.

    :param str user_name:
        Owner of the returned results.
    :returns:
        :class:`django.db.models.query.QuerySet` of
        :class:`openquake.db.models.OqJob` objects, sorted in
        reverse chronological order.
    :rtype:
        :class:`django.db.models.query.QuerySet`
    """
    return models.OqJob.objects.filter(
        owner__user_name=user_name).extra(
            where=["status in ('succeeded', 'failed')"]).order_by(
                '-last_update')


def get_outputs(job_id):
    """Get all :class:`openquake.db.models.Output`s associated with the
    specified job.

    :param int job_id:
        ID of a :class:`openquake.db.models.OqJob`.
    :returns:
        :class:`django.db.models.query.QuerySet` of
        :class:`openquake.db.models.Output` objects.
    """
    return models.Output.objects.filter(oq_job=job_id)


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

    return export_fn(output, os.path.expanduser(target_dir))
