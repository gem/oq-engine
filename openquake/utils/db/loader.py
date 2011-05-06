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

def _read_simple_fault_src():
    pass

def _read_complex_fault_src():
    pass

def _read_area_src():
    pass

def _read_point_src():
    pass

class SourceModelLoader(object):

    def __init__(self, src_model_path, engine):
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

    def serialize(self):
        """
        Read the source model and inject it into the database.

        :returns: number of rows inserted TODO: dict of insertions, keyed by
            tablename?
        """
        insert_data = self.read_model()
        self.write_to_db(insert_data)

    def read_model(self):
        """
        Read the source model data.

        Return a dict of stuff.
        TODO: explain me better, fool
        """
        raise NotImplementedError

    def write_to_db(self, insert_data):
        raise NotImplementedError

class CsvModelLoader(SourceModelLoader):
    def __init__(self, src_model_path, engine, schema):
        super(CsvModelLoader, self).__init__(src_model_path, engine)
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

            # TODO: find a better way to relate catalog/surface, without passing
            # the id to catalog
            surface = self.soup.surface.insert(semi_minor=row['semi_minor'],
                semi_major=row['semi_major'],
                strike=row['strike'])

            self.soup.flush()

            mags = ['mb_val', 'mb_val_error',
                'ml_val', 'ml_val_error',
                'ms_val', 'ms_val_error',
                'mw_val', 'mw_val_error']

            for mag in mags:
                row[mag] = row[mag].strip()

                if len(row[mag]) == 0:
                    row[mag] = -999

                row[mag] = float(row[mag])

            # TODO: find a better way to relate catalog/magnitude, 
            # without passing the id to catalog
            magnitude = self.soup.magnitude.insert(mb_val=row['mb_val'],
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
            self.soup.catalog.insert(owner_id=1, time=timestamp, 
                surface_id=surface.id, eventid=row['eventid'], 
                agency=row['agency'], identifier=row['identifier'], 
                time_error=row['time_error'], depth=row['depth'],
                depth_error=row['depth_error'], magnitude_id=magnitude.id,
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
        return db
