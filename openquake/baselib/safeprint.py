# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from sys import stdout

try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__


def print(*args, **kwargs):
    ret_str = ()
    # when stdout is redirected to a file, python 2 uses ascii for the writer;
    # python 3 uses what is configured in the system (i.e. 'utf-8')
    str_encoding = stdout.encoding if stdout.encoding is not None else 'ascii'
    for s in args:
        ret_str = s.encode('utf-8').decode(str_encoding, 'ignore')

    return __builtin__.print(ret_str, **kwargs)
