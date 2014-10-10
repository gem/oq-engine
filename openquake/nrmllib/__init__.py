# Copyright (c) 2010-2014, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.

"""
NRML base path
"""

NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
GML_NAMESPACE = 'http://www.opengis.net/gml'
SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}


class InvalidFile(Exception):
    pass


class NRMLFile(object):
    """
    Context-managed output object which accepts either a path or a file-like
    object.

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
