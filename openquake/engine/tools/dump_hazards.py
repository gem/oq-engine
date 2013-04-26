#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
A script to dump hazard outputs. If you launch it with a given
hazard_calculation_id, it will dump all the hazard outputs relevant for
risk calculations in a tarfile named hc<hazard-calculation-id>.tar.
The tar file can then be moved around and restored in a different
database. Just untar it and follow the instructions in the README.txt file,
i.e. run the included RESTORE.py file.
Internally the dump and restore procedures are based on
COPY TO and COPY FROM commands, so they are quite performant
even for large datasets. They cannot trivially be extended to perform
binary dump/restore since the geography type has no binary form in
PostGIS 1.5.

To restore a hazard computation and all of its outputs into a new database
run ``python restore_hazards.py <tarfile> <host> <dbname> <user> <password>``

The <user> must have sufficient permissions to write on <dbname>.
The restore will fail if your database already contains a hazard calculation
with the same id. If you think that the hazard calculation on your database
is not important and can removed together with all of its outputs, then
remove it by using ``bin/openquake --delete-hazard-calculation`` (which
must be run by an user with sufficient permissions). Then run again
``restore_hazards.py``.
'''
"""

import os
import shutil
import tarfile
import gzip
import argparse
import psycopg2
import tempfile

THISDIR = os.path.dirname(__file__)


# return a string which is a valid SQL tuple
def _tuplestr(row):
    return '(%s)' % ', '.join(str(x) for x in row)


class Cursor(object):
    """
    Small wrapper around a psycopg2 cursor, which a .copy method
    writing directly to .gz files.
    """
    def __init__(self, psycopg2_cursor):
        self._cursor = psycopg2_cursor

    def tuplestr(self, query, *args):
        "Retrieve tuples of ids a strings"
        self._cursor.execute(query, args)
        return _tuplestr(row[0] for row in self._cursor)

    def fetchall(self, query, *args):
        "Dispatch to .fetchall"
        self._cursor.execute(query, args)
        return self._cursor.fetchall()

    def copy(self, query, dest, name, mode):
        """
        Performs a COPY TO/FROM operation; sql is the query, dest
        is the destination directory, name is the destination name
        and mode is 'w' (for COPY TO) or 'r' (for COPY FROM).
        It works directly with gzipped files.
        """
        fname = os.path.join(dest, name + '.gz')
        print '%s\n(-> %s)' % (query, fname)
        with gzip.open(fname, mode) as f:
            self._cursor.copy_expert(query, f)


def tardir(dirpath, name):
    """
    Tar the contents of a directory into a tarfile and remove the directory
    """
    with tarfile.open(dirpath + '.tar', 'w') as t:
        t.add(dirpath, name)
    shutil.rmtree(dirpath)
    return dirpath + '.tar'


class HazardDumper(object):
    """
    Class to dump a hazard_calculation.
    The important method to call is .dump(hazard_calculation_id).
    """

    @staticmethod
    def filenames(*tnames):
        """
        Return a list .csv.gz filenames
        """
        return ['%s.csv.gz' % tname for tname in tnames]

    def __init__(self, conn, out_dir=None, format='text'):
        self.conn = conn
        self.curs = Cursor(conn.cursor())
        self.format = format
        assert format == 'text', format
        # there is no binary format for geography in postgis 1.5,
        # this is why we are requiring text format
        out_dir = out_dir or tempfile.mkdtemp(prefix='hazard_calculation-')
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.mkdir(out_dir)
        self.dest = out_dir

    def hazard_calculation(self, id_):
        "Dump organization, oq_user, hazard_calculation, lt_realization"
        self.curs.copy(
            """copy (select * from uiapi.hazard_calculation where id=%s)
                  to stdout with (format '%s')""" % (id_, self.format),
            self.dest, 'uiapi.hazard_calculation.csv', 'w')
        self.curs.copy(
            """copy (select * from hzrdr.lt_realization
                  where hazard_calculation_id=%s)
                  to stdout with (format '%s')""" % (id_, self.format),
            self.dest, 'hzrdr.lt_realization.csv', 'w')
        owner_id = self.curs.tuplestr(
            'select owner_id from uiapi.hazard_calculation where id=%s' % id_)
        self.curs.copy(
            """copy (select * from admin.oq_user where id in %s and id != 1)
                  to stdout with (format '%s')""" % (owner_id, self.format),
            self.dest, 'admin.oq_user.csv', 'w')
        org_id = self.curs.tuplestr(
            'select organization_id from admin.oq_user where id in %s'
            % owner_id)
        self.curs.copy(
            """copy (select * from admin.organization where id in %s
            and id != 1) to stdout with (format '%s')""" %
            (org_id, self.format), self.dest, 'admin.organization.csv', 'w')
        return self.filenames(
            'admin.organization', 'admin.oq_user',
            'uiapi.hazard_calculation', 'hzrdr.lt_realization')

    def oq_job(self, id_):
        "Dump oq_job"
        self.curs.copy(
            """copy (select * from uiapi.oq_job where id in %s)
                  to stdout with (format '%s')""" % (id_, self.format),
            self.dest, 'uiapi.oq_job.csv', 'w')
        return self.filenames('uiapi.oq_job')

    def output(self, ids):
        "Dump output"
        self.curs.copy(
            """copy (select * from uiapi.output where id in %s)
                  to stdout with (format '%s')""" % (ids, self.format),
            self.dest, 'uiapi.output.csv', 'w')
        return self.filenames('uiapi.output')

    def hazard_curve(self, output):
        "Dump hazard_curve, hazard_curve_data"
        self.curs.copy(
            """copy (select * from hzrdr.hazard_curve where output_id in %s)
                  to stdout with (format '%s')""" % (output, self.format),
            self.dest, 'hzrdr.hazard_curve.csv', 'w')

        ids = self.curs.tuplestr(
            'select id from hzrdr.hazard_curve where output_id in %s' % output)
        self.curs.copy(
            """copy (select * from hzrdr.hazard_curve_data
                  where hazard_curve_id in {})
                  to stdout with (format '{}')""".format(ids, self.format),
            self.dest, 'hzrdr.hazard_curve_data.csv', 'w')

        return self.filenames(
            'hzrdr.hazard_curve', 'hzrdr.hazard_curve_data')

    def gmf_collection(self, output):
        "Dump gmf_collection, gmf_agg"
        self.curs.copy(
            """copy (select * from hzrdr.gmf_collection
                  where output_id in %s)
                  to stdout with (format '%s')""" % (output, self.format),
            self.dest, 'hzrdr.gmf_collection.csv', 'w')

        coll_ids = self.curs.tuplestr('select id from hzrdr.gmf_collection '
                                      'where output_id in %s' % output)
        self.curs.copy(
            """copy (select * from hzrdr.gmf_agg
                  where gmf_collection_id in %s)
                  to stdout with (format '%s')""" % (coll_ids, self.format),
            self.dest, 'hzrdr.gmf_agg.csv', 'w')

        return self.filenames(
            'hzrdr.gmf_collection', 'hzrdr.gmf_agg')

    def gmf_scenario(self, output):
        "Dump gmf_scenario"
        self.curs.copy("""copy (select * from hzrdr.gmf_scenario
                     where output_id in %s)
                     to stdout with (format '%s')""" % (output, self.format),
                       self.dest, 'hzrdr.gmf_scenario.csv', 'w')
        return self.filenames('hzrdr.gmf_scenario')

    def dump(self, hazard_calculation_id):
        """
        Dump all the data associated to a given hazard_calculation_id
        and relevant for risk.
        """
        curs = self.curs

        # retrieve all the jobs associated to the given calculation
        jobs = curs.tuplestr(
            'select id from uiapi.oq_job where hazard_calculation_id =%s',
            hazard_calculation_id)

        outputs = curs.fetchall("""\
        select output_type, array_agg(id) from uiapi.output
        where oq_job_id in %s group by output_type
        having output_type in ('gmf', 'hazard_curve', 'gmf_scenario')
           """ % jobs)
        if not outputs:
            raise RuntimeError('No outputs for jobs %s' % jobs)

        # collect generated filenames
        filenames = self.hazard_calculation(hazard_calculation_id)
        filenames.extend(self.oq_job(jobs))
        all_outs = sum([output_ids for output_type, output_ids in outputs], [])
        filenames.extend(self.output(_tuplestr(all_outs)))
        for output_type, output_ids in outputs:
            ids = _tuplestr(output_ids)
            if output_type == 'hazard_curve':
                filenames.extend(self.hazard_curve(ids))
            elif output_type == 'gmf':
                filenames.extend(self.gmf_collection(ids))
            elif output_type == 'gmf_scenario':
                filenames.extend(self.gmf_scenario(ids))

        # save FILENAMES.txt
        with open(os.path.join(self.dest, 'FILENAMES.txt'), 'w') as f:
            f.write('\n'.join(filenames))
        # return the pathname of the generated tarfile
        return tardir(self.dest, 'hazard_calculation')


def main(hazard_calculation_id, host='localhost', dbname='openquake',
         user='oq_admin', password=''):
    """
    Dump a hazard_calculation and its relative outputs.
    """
    conn = psycopg2.connect(host=None if host == 'localhost' else host,
                            dbname=dbname, user=user, password=password)
    tar = HazardDumper(conn, 'text').dump(hazard_calculation_id)
    print 'Written %s' % tar


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('hazard_calculation_id')
    p.add_argument('host', nargs='?', default='localhost')
    p.add_argument('dbname', nargs='?', default='openquake')
    p.add_argument('user', nargs='?', default='oq_admin')
    p.add_argument('password', nargs='?', default='')
    arg = p.parse_args()
    main(arg.hazard_calculation_id, arg.host, arg.dbname,
         arg.user, arg.password)
