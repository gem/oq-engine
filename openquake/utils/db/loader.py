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
    Loads:
        * The EQ Catalog
        * PSHA Input Model
"""


import csv
from sqlalchemy.ext.sqlsoup import SqlSoup
import datetime

import geoalchemy

class CsvModelLoader(object):
    def __init__(self, src_model_path, engine, schema):
        """
        :param src_model_path: path to a source model file
        :type src_model_path: str

        :param engine: db engine to provide connectivity and reflection
        :type engine: :py:class:`sqlalchemy.engine.base.Engine`

        :param mfd_bin_width: Magnitude Frequency Distribution bin width
        :type mfd_bin_width: float
        """
        self.src_model_path = src_model_path
        self.engine = engine
        self.soup = self._sql_soup_init(schema)
        self.csv_reader = None
        self.csv_fd = open(self.src_model_path, 'r')

    def read_model(self):
        self.csv_reader = csv.DictReader(self.csv_fd, delimiter=',')

    def serialize(self):
        self.read_model()
        self.write_to_db(self.csv_reader)


    def date_to_timestamp(self, year, month, day, hour, minute, sec):
        """
            Quick helper function to have a timestamp for the
            openquake postgres database
        """
        catalog_date = datetime.datetime(year, month, day, hour, minute, sec)
        return catalog_date.strftime('%Y-%m-%d %H:%M:%S')

    def write_to_db(self, insert_data):

        for row in insert_data:

            timestamp = self.date_to_timestamp(int(row['year']),
                int(row['month']), int(row['day']), int(row['hour']),
                int(row['minute']), int(row['second']))

            surface = self.soup.surface(semi_minor=row['semi_minor'],
                semi_major=row['semi_major'],
                strike=row['strike'])

            # creates the record inside the transaction, no commit yet
            self.soup.flush()

            mags = ['mb_val', 'mb_val_error',
                'ml_val', 'ml_val_error',
                'ms_val', 'ms_val_error',
                'mw_val', 'mw_val_error']

            for mag in mags:
                row[mag] = row[mag].strip()

                # if m*val* are empty or a series of blank spaces, we assume
                # that the val is -999 for convention (ask Graeme if we want to
                # change this)
                if len(row[mag]) == 0:
                    row[mag] = -999

                row[mag] = float(row[mag])

            magnitude = self.soup.magnitude(mb_val=row['mb_val'],
                                mb_val_error=row['mb_val_error'],
                                ml_val=row['ml_val'],
                                ml_val_error=row['ml_val_error'],
                                ms_val=row['ms_val'],
                                ms_val_error=row['ms_val_error'],
                                mw_val=row['mw_val'],
                                mw_val_error=row['mw_val_error'])

            # creates the record inside the transaction, no commit yet
            self.soup.flush()

            wkt = 'POINT(%s %s)' % (row['longitude'], row['latitude'])
            self.soup.catalog(owner_id=1, time=timestamp, 
                surface=surface, eventid=row['eventid'], 
                agency=row['agency'], identifier=row['identifier'], 
                time_error=row['time_error'], depth=row['depth'],
                depth_error=row['depth_error'], magnitude=magnitude,
                point=geoalchemy.WKTSpatialElement(wkt, 4326))

        # commit results
        self.soup.commit()    

    def _sql_soup_init(self, schema):
        """
            Gets the schema to connect
            to the db, creates a SqlSoup instance, sets the schema

            :param schema: database schema
            :type schema: str
        """
        db = SqlSoup(self.engine)
        db.schema = schema
        db.catalog.relate('surface', db.surface)
        db.catalog.relate('magnitude', db.magnitude)
        return db
