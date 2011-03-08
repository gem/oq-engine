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


# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base classes for the output methods of the various codecs.
"""


class FileWriter(object):
    """Simple output half of the codec process."""

    def __init__(self, path):
        self.path = path
        self.file = None
        self._init_file()
        self.root_node = None
    
    def _init_file(self):
        """Get the file handle open for writing"""
        self.file = open(self.path, "w")

    def write(self, point, value):
        """Write out an individual point (unimplemented)"""
        raise NotImplementedError

    def write_header(self):
        """Write out the file header"""
        pass

    def write_footer(self):
        """Write out the file footer"""
        pass


    def close(self):
        """Close and flush the file. Send finished messages."""
        self.file.close()

    def serialize(self, iterable):
        """Wrapper for writing all items in an iterable object."""
        if isinstance(iterable, dict):
            iterable = iterable.items()
        self.write_header()
        for key, val in iterable:
            self.write(key, val)
        self.write_footer()
        self.close()
