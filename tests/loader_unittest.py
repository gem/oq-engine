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
import openquake.utils.db as db
from openquake.utils.db import loader
from tests.utils import helpers

class DbLoaderTestCase(unittest.TestCase):
    """
        Main class to execute tests about NRML/CSV
    """
    def test_csv_to_db_loader_end_to_end(self):
        def _pop_date_fields(csv):
            date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
            res = [csv.pop(csv.index(field)) for field in date_fields]
            return res
                
        def _prepare_date(csv_r, date_fields):
            return [int(csv_r[field]) for field in date_fields]
        def _pop_geometry_fields(csv):
            unused_fields = ['longitude', 'latitude']
            return [csv.pop(csv.index(field)) for field in unused_fields]

        user = 'kpanic'
        password = 'openquake'
        dbname = 'openquake'

        engine = db.create_engine(dbname=dbname ,user=user, password=password)

        csv_file = "ISC_sampledata1.csv"
        csv_path = helpers.get_tests_path(csv_file)
        csv_loader = loader.CsvModelLoader(csv_path, engine, 'eqcat')
        csv_loader.serialize()
        soup_db = csv_loader.soup

        surf_join = soup_db.join(soup_db.catalog, soup_db.surface,
            soup_db.catalog.surface_id==soup_db.surface.id,isouter=False)
        mag_join = soup_db.join(surf_join, soup_db.magnitude,
            soup_db.catalog.magnitude_id==soup_db.magnitude.id, isouter=False)
        #print mag_join.all()
        db_rows = mag_join.order_by(soup_db.catalog.eventid).all()
        # rewind the file
        csv_loader.csv_fd.seek(0)

        # skip the header
        csv_loader.csv_reader.next()
        csv_els = list(csv_loader.csv_reader)
        for csv_row, db_row in zip(csv_els, db_rows):
            csv_keys = csv_row.keys()
            # pops 'longitude', 'latitude' which are used to populate
            # geometry_columns
            _pop_geometry_fields(csv_keys)

            timestamp = _prepare_date(csv_row, _pop_date_fields(csv_keys))
            csv_time = csv_loader.date_to_timestamp(*timestamp)
            # first we compare the timestamps
            self.assertEqual(str(db_row.time), csv_time)
            
            # then, we cycle through the csv keys and consider some special
            # cases
            for csv_key in csv_keys:
                db_val = getattr(db_row, csv_key)
                csv_val = csv_row[csv_key]
                if not len(csv_val.strip()):
                    csv_val = '-999.0'
                if csv_key == 'agency':
                    self.assertEqual(str(db_val), str(csv_val))
                else:
                    self.assertEqual(float(db_val), float(csv_val))
        for db_row in db_rows:
           soup_db.delete(db_row) 
        soup_db.commit()
