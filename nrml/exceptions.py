# Copyright (c) 2010-2012, GEM Foundation.
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


class NrmlError(Exception):
    """Base or general error type for NRML."""


class UnexpectedNamespaceError(NrmlError):
    """A specific error type to indicate that an unexpected namespace was
    encountered.
    """

    _MSG_FMT = "Expected the namespace '%(expected)s', found '%(found)s'."

    def __init__(self, expected, found):
        msg = self._MSG_FMT % dict(expected=expected, found=found)
        super(UnexpectedNamespaceError, self).__init__(msg)


class UnexpectedElementError(NrmlError):
    """A specific error type to indicate that an expected element was
    encountered.
    """

    _MSG_FMT = "Expected '%(expected)s element, found '%(found)s.'"

    def __init__(self, expected, found):
        msg = self._MSG_FMT % dict(expected=expected, found=found)
        super(UnexpectedElementError, self).__init__(msg)
