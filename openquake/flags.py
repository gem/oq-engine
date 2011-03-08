# Copyright (c) 2010-2011, GEM Foundation.
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



"""
Global command-line flags for configuration, plus a wrapper around gflags.
In the future, we may extend this to use either cement, or the nova 
gflags extensions.
"""

# pylint: disable=W0401, W0622, W0614

from gflags import * 
from gflags import FLAGS
from gflags import DEFINE_string
from gflags import DEFINE_boolean, DEFINE_integer

(_, _, _, _) = FLAGS, DEFINE_boolean, DEFINE_integer, DEFINE_string

DEFINE_string('debug', 'warn', 
    'Turns on debug logging and verbose output')
