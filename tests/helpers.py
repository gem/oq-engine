# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Helper classes/functions needed across multiple unit tests.
"""


import os
import tempfile


class TestMixin(object):
    """Mixin class with various helper methods."""

    def touch(self, content=None, dir=None, prefix="tmp", suffix="tmp"):
        """Create temporary file with the given content.

        Please note: the temporary file must be deleted bu the caller.

        :param string content: the content to write to the temporary file.
        :param string dir: directory where the file should be created
        :param string prefix: file name prefix
        :param string suffix: file name suffix
        :returns: a string with the path to the temporary file
        """
        if dir is not None:
            if not os.path.exists(dir):
                os.makedirs(dir)
        fh, path = tempfile.mkstemp(dir=dir, prefix=prefix, suffix=suffix)
        if content:
            fh = os.fdopen(fh, "w")
            fh.write(content)
            fh.close()
        return path
