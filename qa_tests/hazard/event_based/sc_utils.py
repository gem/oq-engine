# Copyright (c) 2014, GEM Foundation.
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

import itertools
import math
from openquake.engine.db import models


def joint_prob_of_occurrence(gmvs_site_1, gmvs_site_2, gmv, time_span,
                             num_ses, delta_gmv=0.1):
    """
    Compute the Poissonian probability of a ground shaking value to be in the
    range [``gmv`` - ``delta_gmv`` / 2, ``gmv`` + ``delta_gmv`` / 2] at two
    different locations within a given ``time_span``.

    :param gmvs_site_1, gmvs_site_2:
        Lists of ground motion values (as floats) for two different sites.
    :param gmv:
        Reference value for computing joint probability.
    :param time_span:
        `investigation_time` parameter from the calculation which produced
        these ground motion values.
    :param num_ses:
        `ses_per_logic_tree_path` parameter from the calculation which produced
        these ground motion values. In other words, the total number of
        stochastic event sets.
    """
    assert len(gmvs_site_1) == len(gmvs_site_2)

    half_delta = float(delta_gmv) / 2
    gmv_close = lambda v: (gmv - half_delta <= v <= gmv + half_delta)
    count = 0
    for gmv_site_1, gmv_site_2 in itertools.izip(gmvs_site_1, gmvs_site_2):
        if gmv_close(gmv_site_1) and gmv_close(gmv_site_2):
            count += 1

    prob = 1 - math.exp(- (float(count) / (time_span * num_ses)) * time_span)
    return prob


# it is important to return the gmvs in a consistent order to be able to
# compare different locations; in other words, the gmvs must correspond to
# the same ruptures in all locations; this is why I am ordering by
# rupture_id; this is used only in the tests (MS)
def get_gmvs_for_location(location, job):
    """
    Get a list of GMVs (as floats) for a given ``location`` and ``job_id``.

    :param str location:
        Location as a POINT string Well Known Text format
    :param job:
        The job that generated the GMVs
    :returns:
        `list` of ground motion values, as floats, sorted by rupture_id
    """
    [output] = job.output_set.filter(output_type='gmf')

    [site] = models.HazardSite.objects.filter(hazard_calculation=job).extra(
        where=["location::geometry ~= 'SRID=4326;%s'::geometry"
               % location])
    gmv_by_rup = {}
    for gmf in models.GmfData.objects.filter(site=site, gmf=output.gmf):
        gmv_by_rup.update(zip(gmf.rupture_ids, gmf.gmvs))

    return [gmv_by_rup[r] for r in sorted(gmv_by_rup)]
