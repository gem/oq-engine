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
        * PSHA
"""

import csv
import sqlalchemy
from sqlalchemy.ext.sqlsoup import SqlSoup
import datetime

import geoalchemy


def sql_soup_init(user, pwd, host, port, database, schema):
    """
        Gets the all the parameters necessary to connect
        to the db, creates a SqlSoup instance, sets the schema
        creates the relationships and returns the db (SqlSoup) instance

        :param user: database username
        :type user: str
        :param pwd: database password
        :type pwd: str
        :param host: database host
        :type host: str
        :param port: database port
        :type port: str
        :param database: database name
        :type database: str
        :param schema: database schema
        :type schema: str


    """
    conn_url = 'postgresql://%s:%s@%s:%s/%s' % (user, pwd,
        host, port, database)
    engine = sqlalchemy.create_engine(conn_url)
    db = SqlSoup(engine)
    db.schema = schema
    db.catalog.relate('magnitude', db.magnitude,
        backref='eqcat.catalog.magnitude_id')
    db.catalog.relate('surface', db.surface, 
        backref='eqcat.catalog.surface_id')
    return db


def eq_catalog_db_import(db, filename):
    """
        Reads from the csv using csv.DictReader, gets the CSV
        input parameters and populates the related 'eqcat' tables

        :param db: the SqlSoup instance that handles all the database
            operations
        :type db: :py:class:`sqlalchemy.ext.sqlsoup.SqlSoup`
        :param filename: the csv input filename
        :type filename: str
    """

    reader = csv.DictReader(open(filename, 'r'), delimiter=',')

    def date_to_timestamp(year, month, day, hour, minute, sec):
        """
            Quick helper function to have a timestamp for the
            openquake postgres database
        """
        catalog_date = datetime.datetime(year, month, day, hour, minute, sec)
        return catalog_date.strftime('%Y-%m-%d %H:%M:%S')

    for row in reader:

        timestamp = date_to_timestamp(int(row['year']),
            int(row['month']), int(row['day']), int(row['hour']),
            int(row['minute']), int(row['second']))

        # TODO: find a better way to relate catalog/surface, without passing
        # the id to catalog
        surface = db.surface.insert(semi_minor=row['semi_minor'],
            semi_major=row['semi_major'],
            strike=row['strike'])

        mags = ['mb_val', 'mb_val_error',
            'ml_val', 'ml_val_error',
            'ms_val', 'ms_val_error',
            'mw_val', 'mw_val_error']

        for mag in mags:
            row[mag] = row[mag].strip()

            if len(row[mag]) == 0:
                row[mag] = -999

            row[mag] = float(row[mag])

        # TODO: find a better way to relate catalog/magnitude, without passing
        # the id to catalog
        magnitude = db.magnitude.insert(mb_val=row['mb_val'],
                            mb_val_error=row['mb_val_error'],
                            ml_val=row['ml_val'],
                            ml_val_error=row['ml_val_error'],
                            ms_val=row['ms_val'],
                            ms_val_error=row['ms_val_error'],
                            mw_val=row['mw_val'],
                            mw_val_error=row['mw_val_error'])

        # creates the record inside the transaction, no commit yet
        db.flush()

        wkt = 'POINT(%s %s)' % (row['longitude'], row['latitude'])
        db.catalog.insert(owner_id=1, time=timestamp, surface_id=surface.id,
            eventid=row['eventid'], agency=row['agency'],
            identifier=row['identifier'], time_error=row['time_error'],
            depth=row['depth'], depth_error=row['depth_error'],
            magnitude_id=magnitude.id,
            point=geoalchemy.WKTSpatialElement(wkt))
