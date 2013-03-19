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
A script to dump hazard outputs. If you launch it with a hazard_calculation_id
it will dump all the hazard outputs relevant for risk calculations in a
zip file named hc<hazard-calculation-id>.zip. The zip file can then be
moved around and restored in a different database. Just unzip it and
follow the instructions in the README.txt file, i.e. run the included
restore.sh file. Internally the dump and restore procedures are based on
COPY TO and COPY FROM commands, so they are quite performant even for
large datasets. They could trivially be extended to perform binary
dump/restore, if needed.
"""

import os
import shutil
import zipfile
import argparse
from django.db import connection

README = '''\
To restore a hazard computation and all of its outputs into a new database,
follow this procedure.

1. go in the directory where this README is
2. run ``source restore.sh``

The restore may fail if your database already contains a hazard calculation
with the same id. If you think that the hazard calculation on your database
is not important and can removed together with all of its outputs, then
remove it by using ``bin/openquake --delete-hazard-calculation`` (which
must be run by an user with sufficient permissions). Then run again
``source restore.sh``.
'''


# return a string which is a valid SQL tuple
def _tuplestr(row):
    return '(%s)' % ', '.join(str(x) for x in row)


class Cursor(object):
    """
    Small wrapper around a psycopg2 cursor
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
        """
        fname = os.path.join(dest, name)
        print '%s (-> %s)' % (query, fname)
        with open(fname, mode) as f:
            self._cursor.copy_expert(query, f)


def zipdir(dirpath):
    """
    Zip the contents of a directory into a zipfile and remove the directory
    """
    with zipfile.ZipFile(dirpath + '.zip', 'w') as z:
        for name in os.listdir(dirpath):
            z.write(os.path.join(dirpath, name))
    shutil.rmtree(dirpath)
    return dirpath + '.zip'


def restore_cmd(*names):
    """
    Return a list of COPY FROM commands
    """
    return ["COPY %s FROM 'PWD/%s.csv';\n" % (name, name.split('.')[-1])
            for name in names]


def dump_hazard_calculation(curs, id_, dest):
    curs.copy("""copy (select * from uiapi.hazard_calculation where id=%s)
              to stdout""" % id_, dest, 'hazard_calculation.csv', 'w')
    curs.copy("""copy (select * from hzrdr.lt_realization
              where hazard_calculation_id=%s)
              to stdout""" % id_, dest, 'lt_realization.csv', 'w')
    return restore_cmd('uiapi.hazard_calculation', 'hzrdr.lt_realization')


def dump_oq_job(curs, id_, dest):
    curs.copy("""copy (select * from uiapi.oq_job where id in %s)
              to stdout""" % id_, dest, 'oq_job.csv', 'w')
    return restore_cmd('uiapi.oq_job')


def dump_output(curs, ids, dest):
    curs.copy("""copy (select * from uiapi.output where id in %s)
              to stdout""" % ids, dest, 'output.csv', 'w')
    return restore_cmd('uiapi.output')


def dump_hazard_curve(curs, output, dest):
    curs.copy("""copy (select * from hzrdr.hazard_curve where output_id in %s)
              to stdout""" % output, dest, 'hazard_curve.csv', 'w')

    ids = curs.tuplestr(
        'select id from hzrdr.hazard_curve where output_id in %s' % output)
    curs.copy("""copy (select * from hzrdr.hazard_curve_data
              where hazard_curve_id in {})
              to stdout""".format(ids), dest, 'hazard_curve_data.csv', 'w')

    return restore_cmd('hzrdr.hazard_curve', 'hzrdr.hazard_curve_data')


def dump_gmf_collection(curs, output, dest):
    curs.copy("""copy (select * from hzrdr.gmf_collection
              where output_id in %s)
              to stdout""" % output, dest, 'gmf_collection.csv', 'w')

    coll_ids = curs.tuplestr('select id from hzrdr.gmf_collection '
                             'where output_id in %s' % output)
    curs.copy("""copy (select * from hzrdr.gmf_set
              where gmf_collection_id in %s)
              to stdout""" % coll_ids, dest, 'gmf_set.csv', 'w')

    set_ids = curs.tuplestr('select id from hzrdr.gmf_set '
                            'where gmf_collection_id in %s' % coll_ids)
    curs.copy("""copy (select * from hzrdr.gmf where gmf_set_id in {})
              to stdout""".format(set_ids), dest, 'gmf.csv', 'w')

    return restore_cmd('hzrdr.gmf_collection', 'hzrdr.gmf_set', 'hzrdr.gmf')


def dump_gmf_scenario(curs, output, dest):
    curs.copy("""copy (select * from hzrdr.gmf_scenario
                 where output_id in %s)
                 to stdout""" % output, dest, 'gmf_scenario.csv', 'w')
    return restore_cmd('hzrdr.gmf_scenario')


def main(hazard_calculation_id):
    """
    Dump a hazard_calculation and its relative outputs.
    """
    out_dir = 'hc%s' % hazard_calculation_id
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.mkdir(out_dir)

    curs = Cursor(connection.cursor().cursor.cursor)

    jobs = curs.tuplestr(
        'select id from uiapi.oq_job where hazard_calculation_id =%s',
        hazard_calculation_id)

    outputs = curs.fetchall("""\
    select output_type, array_agg(id) from uiapi.output
    where oq_job_id in %s group by output_type
    having output_type in ('gmf', 'hazard_curve', 'gmf_scenario')
       """ % jobs)
    if not outputs:
        raise SystemExit('No outputs for jobs %s' % jobs)
    restore = dump_hazard_calculation(curs, hazard_calculation_id, out_dir)
    restore.extend(dump_oq_job(curs, jobs, out_dir))
    all_outs = sum([output_ids for output_type, output_ids in outputs], [])
    restore.extend(dump_output(curs, _tuplestr(all_outs), out_dir))
    for output_type, output_ids in outputs:
        ids = _tuplestr(output_ids)
        if output_type == 'hazard_curve':
            restore.extend(dump_hazard_curve(curs, ids, out_dir))
        elif output_type == 'gmf':
            restore.extend(dump_gmf_collection(curs, ids, out_dir))
        elif output_type == 'gmf_scenario':
            restore.extend(dump_gmf_scenario(curs, ids, out_dir))

    restore_script = os.path.join(out_dir, 'restore.sql')
    with open(restore_script, 'w') as f:
        for cmd in restore:
            f.write(cmd)
    with open(os.path.join(out_dir, 'restore.sh'), 'w') as f:
        f.write('sed -ie "s@PWD@`pwd`@g" restore.sql\n')
        f.write('psql openquake -f restore.sql\n')
    with open(os.path.join(out_dir, 'README.txt'), 'w') as f:
        f.write(README)
    print 'Written %s' % zipdir(out_dir)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('hazard_calculation_id')
    arg = p.parse_args()
    main(arg.hazard_calculation_id)
