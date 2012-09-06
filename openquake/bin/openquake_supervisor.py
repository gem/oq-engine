#! /usr/bin/env python

# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
The OpenQuake job supervisor process, spawned by each OpenQuake job.
"""
import logging
import os
import sys

import oqpath
oqpath.set_oq_path()


def main():  # pylint: disable=C0111
    os.environ['DJANGO_SETTINGS_MODULE'] = 'openquake.settings'

    from openquake.supervising import supervisor

    job_id = int(sys.argv[1])
    pid = int(sys.argv[2])
    supervisor.supervise(pid, job_id)


if __name__ == '__main__':
    main()
