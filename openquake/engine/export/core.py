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

"""Functions for getting information about completed jobs and
calculation outputs, as well as exporting outputs from the database to various
file formats."""


import os

from openquake.engine.db import models


#: Used to separate node labels in a logic tree path
LT_PATH_JOIN_TOKEN = '_'


def _export_fn_not_implemented(output, _target_dir):
    """This gets called if an export is attempted on an unsupported output
    type. See :data:`_EXPORT_FN_MAP`."""
    raise NotImplementedError('Cannot export output of type: %s'
                              % output.output_type)


def makedirsdeco(fn):
    """Decorator for export functions. Creates intermediate directories (if
    necessary) to the target export directory.

    This is equivalent to `mkdir -p` and :func:`os.makedirs`.
    """

    def wrapped(output, target, **kwargs):
        """
        If the the ``target`` is a directory path (string), call
        :func:`os.makedirs` to create intermediate directories to
        the ``target``.

        Otherwise, the ``target`` could be a file-like object, in which case we
        don't do anything.
        """
        if isinstance(target, basestring):
            makedirs(target)
        return fn(output, target, **kwargs)

    # This fixes doc generation problems with decorators
    wrapped.__doc__ = fn.__doc__
    wrapped.__repr__ = fn.__repr__

    return wrapped


def makedirs(path):
    """
    Make all of the directories in the ``path`` using `os.makedirs`.
    """
    if os.path.exists(path):
        if not os.path.isdir(path):
            # If it's not a directory, we can't do anything.
            # This is a problem
            raise RuntimeError('%s already exists and is not a directory.'
                               % path)
    else:
        os.makedirs(path)


def get_outputs(job_id):
    """Get all :class:`openquake.engine.db.models.Output` objects associated
    with the specified job.

    :param int job_id:
        ID of a :class:`openquake.engine.db.models.OqJob`.
    :returns:
        :class:`django.db.models.query.QuerySet` of
        :class:`openquake.engine.db.models.Output` objects.
    """
    return models.Output.objects.filter(oq_job=job_id)
