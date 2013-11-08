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
from openquake.engine.db import models
import logging

log = logging.getLogger()


# return a string which is a valid SQL tuple
def _tuplestr(tup):
    return '(%s)' % ', '.join(str(x) for x in tup)


class Copier(object):
    """
    Small wrapper around a psycopg2 cursor, which a .copy method
    writing directly to csv files. It remembers the copied filenames,
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
        Performs a COPY TO/FROM operation. <Works directly with csv files.

        :param str query: the COPY query
        :param str dest: the destination directory
        :param str name: the destination file name
        :param chr mode: 'w' (for COPY TO) or 'r' (for COPY FROM)
        """
        fname = os.path.join(dest, name)
        log.info('%s\n(-> %s)', query, fname)
        # here is some trick to avoid storing filename and timestamp info
        with open(fname, mode) as fileobj:
            self._cursor.copy_expert(query, fileobj)
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

    def __init__(self, conn, outdir=None):
        self.conn = conn
        self.curs = Copier(conn.cursor())
        outdir = outdir or "/tmp/hc-dump"
        if os.path.exists(outdir):
            # cleanup previously dumped archives, if any
            for fname in os.listdir(outdir):
                if fname.endswith('.csv'):
                    os.remove(os.path.join(outdir, fname))
        else:
            os.mkdir(outdir)
        self.outdir = outdir

    def _copy(self, query, filename, mode='w'):
        self.curs.copy(
            """copy (%s)
               to stdout
               with (format 'csv', header true, encoding 'utf8')""" % query,
            self.outdir, filename, mode)

    def hazard_calculation(self, ids):
        """Dump hazard_calculation, lt_realization, hazard_site"""
        self._copy(
            "select * from uiapi.hazard_calculation where id in %s" % ids,
            'uiapi.hazard_calculation.csv')
        self._copy(
            """select * from hzrdr.lt_realization
               where hazard_calculation_id in %s""" % ids,
            'hzrdr.lt_realization.csv')
        self._copy(
            """select * from hzrdi.hazard_site
               where hazard_calculation_id in %s""" % ids,
               'hzrdi.hazard_site.csv')

    def oq_job(self, ids):
        """Dump hazard_calculation, oq_job"""
        hc_ids = self.curs.tuplestr(
            'select hazard_calculation_id from uiapi.oq_job where id in %s'
            % ids)
        if 'None' in hc_ids:
            raise TypeError('Job %s is not associated to a hazard calculation!'
                            % ids)
        self.hazard_calculation(hc_ids)
        self._copy(
            """select * from uiapi.oq_job where id in %s""" % ids,
            'uiapi.oq_job.csv')

    def output(self, ids):
        """Dump output"""
        self._copy(
            """select * from uiapi.output where id in %s""" % ids,
            'uiapi.output.csv')

    def hazard_curve(self, output):
        """Dump hazard_curve, hazard_curve_data"""
        self._copy(
            """select * from hzrdr.hazard_curve
               where output_id in %s""" % output,
            'hzrdr.hazard_curve.csv', mode='a')

        ids = self.curs.tuplestr(
            'select id from hzrdr.hazard_curve where output_id in %s' % output)

        self._copy(
            """select * from hzrdr.hazard_curve_data
               where hazard_curve_id in {}""".format(ids),
            'hzrdr.hazard_curve_data.csv', mode='a')

    def gmf(self, output):
        """Dump gmf, gmf_data"""
        self._copy(
            """select * from hzrdr.gmf where output_id in %s)""" % output,
               'hzrdr.gmf.csv', mode='a')

        coll_ids = self.curs.tuplestr('select id from hzrdr.gmf '
                                      'where output_id in %s' % output)
        self._copy(
            """select * from hzrdr.gmf_data where gmf_id in %s""" % coll_ids,
            'hzrdr.gmf_data.csv', mode='a')

    def ses(self, output):
        """Dump ses_collection, ses, ses_rupture"""
        self._copy(
            """select * from hzrdr.ses_collection
               where output_id in %s""" % output,
            'hzrdr.ses_collection.csv', 'a')

        coll_ids = self.curs.tuplestr('select id from hzrdr.ses_collection '
                                      'where output_id in %s' % output)
        self._copy(
            """select * from hzrdr.ses
               where ses_collection_id in %s""" % coll_ids,
            'hzrdr.ses.csv', mode='a')

        ses_ids = self.curs.tuplestr(
            'select id from hzrdr.ses where ses_collection_id in %s'
            % coll_ids)
        self._copy(
            """select * from hzrdr.ses_rupture where ses_id in %s""" % ses_ids,
            'hzrdr.ses_rupture.csv', 'a')

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
            print "Dumping %s %s in %s" % (output_type, ids, self.outdir)
            if output_type == 'ses':
                self.ses(ids)
            else:
                log.warn("Unsupported output type %s" % output_type)
        # save FILENAMES.txt
        filenames = os.path.join(
            self.outdir, 'FILENAMES.txt')
        with open(filenames, 'w') as f:
            f.write('\n'.join(map(os.path.basename, self.curs.filenames)))


def main(hazard_calculation_id, outdir=None):
    """
    Dump a hazard_calculation and its relative outputs
    """
    logging.basicConfig(level=logging.WARN)
    hc = HazardDumper(models.getcursor('admin').connection, outdir)
    hc.dump(hazard_calculation_id)
    log.info('Written %s' % hc.outdir)
    return hc.outdir
