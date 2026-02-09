# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025-2026 GEM Foundation
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

from openquake.commonlib import logs

def failing():
    try:
        1/0
    except:
        print('Found an error')
        raise


def test_error():
    dic = dict(description="A failing job", calculation_mode="custom")
    job = logs.init(dic)
    try:
        with job:
            failing()
    except ZeroDivisionError:
        pass
    tb_lines = logs.dbcmd('get_traceback', job.calc_id)
    print('\n'.join(tb_lines))
