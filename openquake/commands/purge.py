# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2019 GEM Foundation
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
import os
import re
import getpass
import shutil
from openquake.baselib import sap, datastore
from openquake.commonlib.logs import dbcmd

datadir = datastore.get_datadir()


def purge_one(calc_id, user):
    """
    Remove one calculation ID from the database and remove its datastore
    """
    filename = os.path.join(datadir, 'calc_%s.hdf5' % calc_id)
    err = dbcmd('del_calc', calc_id, user)
    if err:
        print(err)
    elif os.path.exists(filename):  # not removed yet
        os.remove(filename)
        print('Removed %s' % filename)


# used in the reset command
def purge_all(user=None, fast=False):
    """
    Remove all calculations of the given user
    """
    user = user or getpass.getuser()
    if os.path.exists(datadir):
        if fast:
            shutil.rmtree(datadir)
            print('Removed %s' % datadir)
        else:
            for fname in os.listdir(datadir):
                mo = re.match('calc_(\d+)\.hdf5', fname)
                if mo is not None:
                    calc_id = int(mo.group(1))
                    purge_one(calc_id, user)


@sap.script
def purge(calc_id):
    """
    Remove the given calculation. If you want to remove all calculations,
    use oq reset.
    """
    if calc_id < 0:
        try:
            calc_id = datastore.get_calc_ids(datadir)[calc_id]
        except IndexError:
            print('Calculation %d not found' % calc_id)
            return
    purge_one(calc_id, getpass.getuser())


purge.arg('calc_id', 'calculation ID', type=int)
