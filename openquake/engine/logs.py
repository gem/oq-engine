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


"""
Set up some system-wide loggers
"""
import logging


# Place the new level between info and warning
logging.PROGRESS = 25
logging.addLevelName(logging.PROGRESS, "PROGRESS")

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warn': logging.WARNING,
          'progress': logging.PROGRESS,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

LOG = logging.getLogger()


def _log_progress(msg, *args, **kwargs):
    """
    Log the message using the progress reporting logging level.

    ``args`` and ``kwargs`` are the same as :meth:`logging.Logger.debug`,
    except that this method has an additional possible keyword: ``indent``.

    Normally, progress messages are logged with a '** ' prefix. If ``indent``
    is `True`, messages will be logged with a '**  >' prefix.

    If ``indent`` is not specified, it will default to `False`.
    """
    indent = kwargs.get('indent')

    if indent is None:
        indent = False
    else:
        # 'indent' is an invalid kwarg for the logger's _log method
        # we need to remove it before we call _log:
        del kwargs['indent']

    if indent:
        prefix = '**  >'
    else:
        prefix = '** '

    msg = '%s %s' % (prefix, msg)
    LOG._log(logging.PROGRESS, msg, args, **kwargs)
LOG.progress = _log_progress


def set_level(level):
    """
    Initialize logs to write records with level `level` or above.
    """
    logging.root.setLevel(LEVELS.get(level, logging.WARNING))


class tracing(object):
    """
    Simple context manager util to handle tracing. E.g.

    with log("exports"):
       do_export()
    """
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        LOG.info('starting %s' % self.msg)

    def __exit__(self, *args, **kwargs):
        LOG.debug('done with %s' % self.msg)
