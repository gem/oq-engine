#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2012-2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os


# this is used in celeryconfig.py
def get_core_modules(pkg):
    """
    :param pkg: a Python package
    :return: a sorted list of the fully qualified module names ending in "core"
    """
    modules = []
    pkgdir = pkg.__path__[0]
    for name in os.listdir(pkgdir):
        fullname = os.path.join(pkgdir, name)
        if os.path.isdir(fullname) and os.path.exists(
                os.path.join(fullname, '__init__.py')):  # is subpackage
            if os.path.exists(os.path.join(fullname, 'core.py')):
                modules.append('%s.%s.core' % (pkg.__name__, name))
    return sorted(modules)


class FileWrapper(object):
    """
    Context-managed object which accepts either a path or a file-like object.

    Behaves like a file.
    """

    def __init__(self, dest, mode='r'):
        self._dest = dest
        self._mode = mode
        self._file = None

    def __enter__(self):
        if isinstance(self._dest, (basestring, buffer)):
            self._file = open(self._dest, self._mode)
        else:
            # assume it is a file-like; don't change anything
            self._file = self._dest
        return self._file

    def __exit__(self, *args):
        self._file.close()
