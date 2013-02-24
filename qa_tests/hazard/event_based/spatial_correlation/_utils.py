# Copyright (c) 2010-2013, GEM Foundation.
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


def joint_prob_of_occurrence(gmfs_site_1, gmfs_site_2, gmf_value,
                             delta_gmv=0.1):
    half_delta = float(delta_gmv) / 2
    gmv_close = lambda v: (gmf_value - half_delta <= v
                           <= gmf_value + half_delta)
    count = 0
    # for v1, v2 in zip(gmfs[0,:], gmfs[1,:]):
    for v1, v2 in zip(gmfs_site_1, gmfs_site_2):
        if gmv_close(v1) and gmv_close(v2):
            count += 1

    prob = float(count) / num_total_gmfs
    return prob
