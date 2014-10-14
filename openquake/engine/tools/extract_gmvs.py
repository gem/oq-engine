# -*- coding: utf-8 -*-

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


"""
Extract ground motion values generated from a hazard calculation and
display them to standard output in CSV format
"""

import sys
import csv
from openquake.engine.db import models
from openquake.hazardlib.imt import from_string


def extract(hc_id, a_writer):
    hc = models.oqparam(hc_id)

    for lt in models.LtRealization.objects.filter(
            lt_model__hazard_calculation=hc.oqjob):

        for imt in hc.intensity_measure_types:
            imt_type, sa_period, _ = from_string(imt)

            if imt_type == "PGA":
                imt_type_fix = "SA"
                sa_period_fix = 0
            else:
                imt_type_fix = imt_type
                sa_period_fix = sa_period

            ruptures = sorted(
                [r.id for r in models.SESRupture.objects.filter(
                    rupture__ses_collection__lt_realization=lt)])

            for site in hc.hazardsite_set.all().order_by('id'):
                gmvs = []
                gmvs_data = dict()

                for ses_coll in models.SESCollection.objects.filter(
                        lt_realization=lt).order_by('id'):
                    for ses in ses_coll:
                        for gmf in models.GmfData.objects.filter(
                                ses_id=ses.ordinal,
                                site=site,
                                imt=imt_type, sa_period=sa_period):
                            gmvs_data.update(
                                dict(zip(gmf.rupture_ids, gmf.gmvs)))
                gmvs.extend([gmvs_data.get(r, 0.0) for r in ruptures])
                a_writer.writerow([lt.id, site.location.x, site.location.y,
                                   imt_type_fix, sa_period_fix] + gmvs)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help']:
        print "Usage:\n %s <hazard_calculation ID>" % sys.argv[0]
        sys.exit(1)

    extract(sys.argv[1], csv.writer(sys.stdout, delimiter=','))
