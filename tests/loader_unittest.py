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
    Unittests for NRML/CSV input files loaders to the database
"""


import unittest
from openquake.utils.db.loader import sql_soup_init
from openquake.utils.db.loader import eq_catalog_db_import
from tests.utils import helpers

class DbLoaderTestCase(unittest.TestCase):
    """
        Main class to execute tests about NRML/CSV
    """
    def test_csv_to_db_loader_end_to_end(self):
        csv_file = "ISC_sampledata1.csv"
        csv_path = helpers.get_tests_path(csv_file)
        db = sql_soup_init('kpanic', 'openquake', 'localhost', '5432',
            'openquake', 'eqcat')
        eq_catalog_db_import(db, csv_path)
        db.commit()
        surf_join = db.join(db.catalog, db.surface,
            db.catalog.surface_id==db.surface.id,isouter=False)
        mag_join = db.join(surf_join, db.magnitude,
            db.catalog.magnitude_id==db.magnitude.id, isouter=False)
        #print mag_join.all()
        print dir(mag_join)
        res = mag_join.all()
        for row in res:
            print row.agency, row.strike

        print len(res)
        self.assertTrue(False)
