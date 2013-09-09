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
risk calculations in a directory named hc<hazard-calculation-id>.
The directory can then be moved around and restored in a different
database with the companion script restore_hazards.py.
Internally the dump and restore procedures are based on
COPY TO and COPY FROM commands, so they are quite performant
even for large datasets. They cannot trivially be extended to perform
binary dump/restore since the geography type has no binary form in
PostGIS 1.5.

To restore a hazard computation and all of its outputs into a new database
run ``python restore_hazards.py <directory> <host> <dbname> <user> <password>``

The <user> must have sufficient permissions to write on <dbname>.  If
your database already contains a hazard calculation with the same id,
the restore will not override it. If you think that the hazard
calculation on your database is not important and can removed together
with all of its outputs, then remove it by using ``bin/openquake
--delete-hazard-calculation`` (which must be run by a user with
sufficient permissions). Then run again ``restore_hazards.py``.
"""

import os
import shutil
import tarfile
import gzip
import argparse
import psycopg2
import tempfile
import logging

log = logging.getLogger()


# return a string which is a valid SQL tuple
def _tuplestr(tup):
    return '(%s)' % ', '.join(str(x) for x in tup)


class Copier(object):
    """
    Small wrapper around a psycopg2 cursor, which a .copy method
    writing directly to .gz files. It remembers the copied filenames,
    which are stored in the attribute .filenames.
    """
    def __init__(self, psycopg2_cursor):
        self._cursor = psycopg2_cursor
        self.filenames = []

    def tuplestr(self, query, *args):
        """Retrieve tuples of ids a strings"""
        self._cursor.execute(query, args)
        return _tuplestr(row[0] for row in self._cursor)

    def fetchall(self, query, *args):
        """Dispatch to .fetchall"""
        self._cursor.execute(query, args)
        return self._cursor.fetchall()

    def copy(self, query, dest, name, mode):
        """
        Performs a COPY TO/FROM operation. <Works directly with gzipped files.

        :param str query: the COPY query
        :param str dest: the destination directory
        :param str name: the destination file name (no .gz)
        :param chr mode: 'w' (for COPY TO) or 'r' (for COPY FROM)
        """
        fname = os.path.join(dest, name + '.gz')
        log.info('%s\n(-> %s)', query, fname)
        with gzip.open(fname, mode) as f:
            self._cursor.copy_expert(query, f)
            if fname not in self.filenames:
                self.filenames.append(fname)


class HazardDumper(object):
    """
    Class to dump a hazard_calculation and related tables.
    The typical usage is

     hd = HazardDumper(conn, '/tmp/somedir')
     hd.dump(42)  # dump the hazard computation #42
     print hd.mktar()  # generate a tarfile
    """

    def __init__(self, conn, outdir=None, format='text'):
        self.conn = conn
        self.curs = Copier(conn.cursor())
        self.format = format
        # there is no binary format for geography in postgis 1.5,
        # this is why we are requiring text format
        assert format == 'text', format
        if outdir:
            os.mkdir(outdir)
        else:
            outdir = tempfile.mkdtemp(prefix='hazard_calculation-')
        self.outdir = outdir

    def hazard_calculation(self, ids):
        """Dump hazard_calculation, lt_realization, hazard_site"""
        self.curs.copy(
            """copy (select * from uiapi.hazard_calculation where id in %s)
                  to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'uiapi.hazard_calculation.csv', 'w')
        self.curs.copy(
            """copy (select * from hzrdr.lt_realization
                  where hazard_calculation_id in %s)
                  to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'hzrdr.lt_realization.csv', 'w')
        self.curs.copy(
            """copy (select * from hzrdi.hazard_site
                  where hazard_calculation_id in %s)
                  to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'hzrdi.hazard_site.csv', 'w')

        # model_content, inputs

        # at this moment, only logic tree content is needed
        self.curs.copy(
            """copy (select mc.* from uiapi.model_content mc
                     join uiapi.input as input
                     on input.model_content_id = mc.id
                     join uiapi.input2hcalc h2c
                     on h2c.input_id = input.id
                     where h2c.hazard_calculation_id = %s
                     and input.input_type in ('source_model_logic_tree',
                                              'gsim_logic_tree'))
               to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'uiapi.model_content.csv', 'w')

        input_ids = self.curs.tuplestr(
            """select i.* from uiapi.input i
                     join uiapi.input2hcalc h2c
                     on h2c.input_id = i.id
                     where hazard_calculation_id in %s
                     and input_type in ('source_model_logic_tree',
                                        'gsim_logic_tree')""" % ids)
        if input_ids != "()":  # scenario calcs do not have logic tree inputs
            self.curs.copy(
                """copy (select * from uiapi.input where id in %s)
                   to stdout with (format '%s')""" % (input_ids, self.format),
                self.outdir, 'uiapi.input.csv', 'w')

            self.curs.copy(
                """copy (select * from uiapi.input2hcalc where input_id in %s)
                   to stdout with (format '%s')""" % (input_ids, self.format),
                self.outdir, 'uiapi.input2hcalc.csv', 'w')

    def performance(self, *job_ids):
        """Dump performance"""
        ids = _tuplestr(job_ids)
        self.oq_job(ids)
        self.curs.copy(
            """copy (select * from uiapi.performance where oq_job_id in %s)
                  to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'uiapi.performance.csv', 'w')

    def oq_job(self, ids):
        """Dump organization, oq_user, hazard_calculation, oq_job"""
        owner_ids = self.curs.tuplestr(
            'select owner_id from uiapi.oq_job where id in %s' % ids)
        org_ids = self.curs.tuplestr(
            'select organization_id from admin.oq_user where id in %s'
            % owner_ids)
        self.curs.copy(
            """copy (select * from admin.organization where id in %s)
               to stdout with (format '%s')""" %
            (org_ids, self.format), self.outdir, 'admin.organization.csv', 'w')
        self.curs.copy(
            """copy (select * from admin.oq_user where id in %s)
               to stdout with (format '%s')""" % (owner_ids, self.format),
            self.outdir, 'admin.oq_user.csv', 'w')

        hc_ids = self.curs.tuplestr(
            'select hazard_calculation_id from uiapi.oq_job where id in %s'
            % ids)
        if 'None' in hc_ids:
            raise TypeError('Job %s is not associated to a hazard calculation!'
                            % ids)
        self.hazard_calculation(hc_ids)
        self.curs.copy(
            """copy (select * from uiapi.oq_job where id in %s)
               to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'uiapi.oq_job.csv', 'w')

    def output(self, ids):
        """Dump output"""
        self.curs.copy(
            """copy (select * from uiapi.output where id in %s)
                  to stdout with (format '%s')""" % (ids, self.format),
            self.outdir, 'uiapi.output.csv', 'a')

    def hazard_curve(self, output):
        """Dump hazard_curve, hazard_curve_data"""
        self.curs.copy(
            """copy (select * from hzrdr.hazard_curve where output_id in %s)
                  to stdout with (format '%s')""" % (output, self.format),
            self.outdir, 'hzrdr.hazard_curve.csv', 'a')

        ids = self.curs.tuplestr(
            'select id from hzrdr.hazard_curve where output_id in %s' % output)

        self.curs.copy(
            """copy (select * from hzrdr.hazard_curve_data
                  where hazard_curve_id in {})
                  to stdout with (format '{}')""".format(ids, self.format),
            self.outdir, 'hzrdr.hazard_curve_data.csv', 'a')

    def gmf(self, output):
        """Dump gmf, gmf_data"""
        self.curs.copy(
            """copy (select * from hzrdr.gmf
                  where output_id in %s)
                  to stdout with (format '%s')""" % (output, self.format),
            self.outdir, 'hzrdr.gmf.csv', 'a')

        coll_ids = self.curs.tuplestr('select id from hzrdr.gmf '
                                      'where output_id in %s' % output)
        self.curs.copy(
            """copy (select * from hzrdr.gmf_data
                  where gmf_id in %s)
                  to stdout with (format '%s')""" % (coll_ids, self.format),
            self.outdir, 'hzrdr.gmf_data.csv', 'a')

    def ses(self, output):
        """Dump ses_collection, ses, ses_rupture"""
        self.curs.copy(
            """copy (select * from hzrdr.ses_collection
                  where output_id in %s)
                  to stdout with (format '%s')""" % (output, self.format),
            self.outdir, 'hzrdr.ses_collection.csv', 'a')

        coll_ids = self.curs.tuplestr('select id from hzrdr.ses_collection '
                                      'where output_id in %s' % output)
        self.curs.copy(
            """copy (select * from hzrdr.ses
                  where ses_collection_id in %s)
                  to stdout with (format '%s')""" % (coll_ids, self.format),
            self.outdir, 'hzrdr.ses.csv', 'a')

        ses_ids = self.curs.tuplestr(
            'select id from hzrdr.ses where ses_collection_id in %s'
            % coll_ids)
        self.curs.copy(
            """copy (select * from hzrdr.ses_rupture
                  where ses_id in %s)
                  to stdout with (format '%s')""" % (ses_ids, self.format),
            self.outdir, 'hzrdr.ses_rupture.csv', 'a')

    def dump(self, *hazard_calculation_ids):
        """
        Dump all the data associated to a given hazard_calculation_id
        and relevant for risk.
        """
        ids = _tuplestr(hazard_calculation_ids)
        curs = self.curs

        # retrieve the last job associated to the given calculation
        jobs = curs.tuplestr(
            'select max(id) from uiapi.oq_job '
            'where hazard_calculation_id in %s' % ids)

        outputs = curs.fetchall("""\
        select output_type, array_agg(id) from uiapi.output
        where oq_job_id in %s group by output_type
        having output_type in ('hazard_curve', 'hazard_curve_multi',
                               'ses', 'gmf', 'gmf_scenario')
           """ % jobs)
        if not outputs:
            raise RuntimeError('No outputs for job %s' % jobs)

        # sort the outputs to prevent foreign key errors
        ordering = {
            'hazard_curve': 1,
            'hazard_curve_multi': 2,
            'ses': 1,
            'gmf': 2,
            'gmf_scenario': 2
        }
        outputs = sorted(outputs, key=lambda o: ordering[o[0]])

        # dump data and collect generated filenames
        self.oq_job(jobs)
        all_outs = sum([output_ids for output_type, output_ids in outputs], [])
        self.output(_tuplestr(all_outs))
        for output_type, output_ids in outputs:
            ids = _tuplestr(output_ids)
            print "Dumping %s %s" % (output_type, ids)
            if output_type in ['hazard_curve', 'hazard_curve_multi']:
                self.hazard_curve(ids)
            elif output_type in ('gmf', 'gmf_scenario'):
                self.gmf(ids)
            elif output_type == 'ses':
                self.ses(ids)
        # save FILENAMES.txt
        filenames = os.path.join(
            self.outdir, 'FILENAMES.txt')
        with open(filenames, 'w') as f:
            f.write('\n'.join(map(os.path.basename, self.curs.filenames)))

    # this is not used right now; the functionality could be restored in
    # the future (optionally)
    def mktar(self):
        """
        Tar the contents of outdir into a tarfile and remove the directory
        """
        # tar outdir
        with tarfile.open(self.outdir + '.tar', 'w') as t:
            t.add(self.outdir)
        shutil.rmtree(self.outdir)
        # return pathname of the generated tarfile
        tarname = self.outdir + '.tar'
        logging.info('Generated %s', tarname)
        return tarname


def main(hazard_calculation_id, outdir=None,
         host='localhost', dbname='openquake',
         user='admin', password='', port=None):
    """
    Dump a hazard_calculation and its relative outputs
    """
    # this is not using the predefined Django connections since
    # the typical use case is to dump from a remote database
    logging.basicConfig(level=logging.INFO)
    conn = psycopg2.connect(
        host=host, database=dbname, user=user, password=password, port=port)
    hc = HazardDumper(conn, outdir)
    hc.dump(hazard_calculation_id)
    log.info('Written %s' % hc.outdir)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('hazard_calculation_id')
    p.add_argument('outdir')
    p.add_argument('host', nargs='?', default='localhost')
    p.add_argument('dbname', nargs='?', default='openquake')
    p.add_argument('user', nargs='?', default='oq_admin')
    p.add_argument('password', nargs='?', default='openquake')
    p.add_argument('port', nargs='?', default='5432')
    arg = p.parse_args()
    main(arg.hazard_calculation_id, arg.outdir, arg.host,
         arg.dbname, arg.user, arg.password, arg.port)
