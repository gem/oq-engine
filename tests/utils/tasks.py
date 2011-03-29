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
Task functions for our unit tests.
"""


from celery.decorators import task

from tests.utils import helpers


@task
def test_data_reflector_task(job_id, *args, **kwargs):
    """Throw back the data stored in the KVS for the given `job_id`.

    This should be used for testing purposes only. The idea is to store the
    data expected in test setup and then use this task to play that data back
    to the test.

    See :py:class:`DoHazardTestCase` for an example of how this task should be
    used.
    """
    return helpers.TestStore.lookup(job_id)
