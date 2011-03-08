# Copyright (c) 2011, GEM Foundation.
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
Constants and helper functions for the output generation.
Includes simple serializers for test harnesses."""

from openquake import writer

class SimpleOutput(writer.FileWriter):
    """Fake output class that writes to stdout."""
    
    def _init_file(self):
        pass
    
    def close(self):
        pass
    
    def write(self, cell, value):
        print "%s : %s" % (cell, value)
    
    def serialize(self, someiterable):
        """Dump all the values of a given iterable"""
        for somekey, somevalue in someiterable.items():
            print "%s : %s" % (somekey, somevalue)