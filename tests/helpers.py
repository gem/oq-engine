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

from tests.utils.helpers import create_job


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

    def create_job_with_mixin(self, params, mixin_class):
        """
        Create a Job and mixes in a Mixin.

        This method, and its double `unload_job_mixin`, when called in the
        setUp and tearDown of a TestCase respectively, have the effect of a
        `with mixin_class` spanning a single test.

        :param params: Job parameters
        :type params: :py:class:`dict`
        :param mixin_class: the mixin that will be mixed in the job
        :type mixin_class: :py:class:`openquake.job.Mixin`
        :returns: a Job
        :rtype: :py:class:`openquake.job.Job`
        """
        # preserve some status to be used by unload
        self._calculation_mode = params.get('CALCULATION_MODE')
        self._job = create_job(params)
        self._mixin = mixin_class(self._job, mixin_class)
        return self._mixin._load()

    def unload_job_mixin(self):
        """
        Remove from the job the Mixin mixed in by create_job_with_mixin.
        """
        self._job.params['CALCULATION_MODE'] = self._calculation_mode
        self._mixin._unload()
