# Copyright (c) 2010-2012, GEM Foundation.
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


from openquake.db import models


def get_calculations(user_name):
    """Get the completed calculations (successful and failed) for the given
    user_name.

    Results are given in reverse chronological order.

    :param str user_name:
        Owner of the returned results.
    :returns:
        A list of :class:`openquake.db.models.OqCalculation` objects, sorted in
        reverse chronological order.

        If there are no results, an empty list is returned.
    """
    return models.OqCalculation.objects.filter(
        owner__user_name=user_name).extra(
            where=["status in ('succeeded', 'failed')"]).order_by(
                '-last_update')


def get_outputs(calculation_id):
    """ """

def export(output_id, target_dir):
    """ """
