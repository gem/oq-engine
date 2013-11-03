import gzip
import psycopg2
import argparse
import logging
import io
import os
import sys

from openquake.engine.db import models
from django.db.models import fields

BLOCKSIZE = 1000  # restore blocks of 1,000 lines each

log = logging.getLogger()


def quote_unwrap(name):
    if name.startswith("\""):
        return name[1:-1]
    else:
        return name


def restore_tablename(original_tablename):
    _schema, tname = map(quote_unwrap, original_tablename.split('.'))
    return "htemp.restore_%s" % tname


class CSVInserter(object):
    def __init__(self, curs, original_tablename, blocksize):
        self.curs = curs
        self.original_tablename = original_tablename
        self.tablename = restore_tablename(original_tablename)
        self.blocksize = blocksize
        self.max_id = 0
        self.io = io.StringIO()
        self.nlines = 0

    def write(self, id_, line):
        """
        Add a csv line.
        """
        self.max_id = max(self.max_id, id_)
        self.io.write('%d\t%s' % (id_, line.decode('utf8')))
        self.nlines += 1
        if self.max_id % self.blocksize == 0:
            self.insert()

    def insert(self):
        """
        Bulk insert into the database in a single transaction
        """
        self.io.seek(0)
        conn = self.curs.connection
        try:
            self.curs.execute("DROP TABLE IF EXISTS %s" % self.tablename)
            self.curs.execute(
                "CREATE TABLE %s AS SELECT * FROM %s WHERE 0 = 1" % (
                    self.tablename, self.original_tablename))
            self.curs.copy_from(self.io, self.tablename)
        except Exception as e:
            conn.rollback()
            log.error(str(e))
            raise
        else:
            conn.commit()
        self.io.truncate(0)
        self.io.seek(0)
        self.max_id = 0

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        if self.max_id:  # some remaining line
            self.insert()


def transfer_data(curs, model, **foreign_keys):
    def model_table(model, restore=False):
        original_tablename = "\"%s\"" % model._meta.db_table
        if restore:
            return restore_tablename(original_tablename)
        else:
            return "{}.{}".format(
                *map(quote_unwrap, original_tablename.split('.')))

    def model_fields(model):
        fs = ", ".join([f.column for f in model._meta.fields
                        if f.column != "id"
                        if not isinstance(f, fields.related.ForeignKey)])
        if fs:
            fs = ", " + fs
        return fs

    conn = curs.connection

    curs.execute(
        "ALTER TABLE %s ADD restore_id INT" % model_table(model))
    args = dict(
        table=model_table(model),
        fields=model_fields(model),
        restore_table=model_table(model, restore=True),
        fk_fields="", fk_joins="", new_fk_ids="")

    if foreign_keys:
        for fk, id_mapping in foreign_keys.iteritems():
            if fk is not None:
                curs.execute(
                    "CREATE TABLE temp_%s_translation("
                    "%s INT NOT NULL, new_id INT NOT NULL)" % (fk, fk))
                ids = ", ".join(["(%d, %d)" % (old_id, new_id)
                                 for old_id, new_id in id_mapping])
                curs.execute(
                    "INSERT INTO temp_%s_translation VALUES %s" % (fk, ids))

                args['fk_fields'] += ", %s" % fk
                args['fk_joins'] += (
                    "JOIN temp_%s_translation USING(%s) " % (fk, fk))
                args['new_fk_ids'] += ", temp_%s_translation.new_id" % fk

    query = """
INSERT INTO %(table)s (restore_id %(fields)s %(fk_fields)s)
SELECT id %(fields)s %(new_fk_ids)s
FROM %(restore_table)s AS restore
%(fk_joins)s
RETURNING  restore_id, %(table)s.id
""" % args

    curs.execute(query)
    old_new_ids = tuple(curs.fetchall())
    curs.execute(
        "ALTER TABLE %s DROP restore_id" % model_table(model))

    for fk in foreign_keys:
        curs.execute("DROP TABLE temp_%s_translation" % fk)

    conn.commit()

    return old_new_ids


def safe_restore(curs, gzfile, tablename, blocksize=BLOCKSIZE):
    """
    Restore a gzipped postgres table into the database, by skipping
    the ids which are already taken. Assume that the first field of
    the table is an integer id and that gzfile.name has the form
    '/some/path/tablename.csv.gz'
    The file is restored in blocks to avoid memory issues.

    :param curs: a psycopg2 cursor
    :param gzfile: a file object
    :param str tablename: full table name
    :param int blocksize: number of lines in a block
    """
    # keep in memory the already taken ids
    with CSVInserter(curs, tablename, blocksize) as csvi:
        total = 0
        for line in gzfile:
            total += 1
            sid, rest = line.split('\t', 1)
            id_ = int(sid)
            csvi.write(id_, rest)
    return csvi.nlines, total


def hazard_restore(conn, directory):
    """
    Import a tar file generated by the HazardDumper.

    :param conn: the psycopg2 connection to the db
    :param directory: the pathname to the directory with the .gz files
    """
    filenames = os.path.join(directory, 'FILENAMES.txt')
    curs = conn.cursor()

    created = []
    for line in open(filenames):
        fname = line.rstrip()
        tname = fname[:-7]  # strip .csv.gz

        fullname = os.path.join(directory, fname)
        with gzip.GzipFile(fname, fileobj=open(fullname)) as f:
            log.info('Importing %s...', fname)
            created.append(tname)
            imported, total = safe_restore(curs, f, tname)
            if imported != total:
                raise RuntimeError(
                    "ID Clash detected. The database might be corrupted")
            log.info(
                "Created %s rows in %s" % (
                    imported, restore_tablename(tname)))
    hc_ids = transfer_data(curs, models.HazardCalculation)
    lt_ids = transfer_data(
        curs, models.LtRealization, hazard_calculation_id=hc_ids)
    transfer_data(
        curs, models.HazardSite, hazard_calculation_id=hc_ids)
    job_ids = transfer_data(
        curs, models.OqJob, hazard_calculation_id=hc_ids)
    out_ids = transfer_data(
        curs, models.Output, oq_job_id=job_ids)
    ses_collection_ids = transfer_data(
        curs, models.SESCollection,
        output_id=out_ids, lt_realization_id=lt_ids)
    ses_ids = transfer_data(
        curs, models.SES, ses_collection_id=ses_collection_ids)
    transfer_data(curs, models.SESRupture, ses_id=ses_ids)

    curs = conn.cursor()
    for tname in reversed(created):
        query = "DROP TABLE %s" % restore_tablename(tname)
        curs.execute(query)
        log.info("Dropped %s" % restore_tablename(tname))
    conn.commit()
    log.info('Restored %s', directory)
    return [new_id for _, new_id in hc_ids]


def hazard_restore_remote(tar, host, dbname, user, password, port):
    conn = psycopg2.connect(
        host=host, dbname=dbname, user=user, password=password, port=port)
    ret = hazard_restore(conn, tar)
    conn.close()
    return ret


def django_restore(tar):
    from django.db import connection
    if connection.connection:
        return hazard_restore(connection.connection, tar)
    else:
        return hazard_restore_local(tar)


def hazard_restore_local(*argv):
    """
    Use the current django settings to restore hazard
    """
    from openquake.engine.db.models import set_django_settings_module
    set_django_settings_module()
    from django.conf import settings
    default_cfg = settings.DATABASES['default']
    host = default_cfg['HOST'] or 'localhost'
    name = default_cfg['NAME']
    user = default_cfg['USER']
    pwd = default_cfg['PASSWORD']
    port = str(default_cfg['PORT'] or 5432)

    def h(dflt):
        return 'default: %s' % dflt

    p = argparse.ArgumentParser()
    p.add_argument('directory', help='mandatory argument')
    p.add_argument('host', nargs='?', default=host, help=h(host))
    p.add_argument('dbname', nargs='?', default=name, help=h(name))
    p.add_argument('user', nargs='?', default=user, help=h(user))
    p.add_argument('password', nargs='?', default=pwd, help=h(pwd))
    p.add_argument('port', nargs='?', default=port, help=h(port))
    arg = p.parse_args(argv)

    return hazard_restore_remote(arg.directory, arg.host, arg.dbname,
                                 arg.user, arg.password, arg.port)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    log.warn("This script restore only Stochastic event set outputs")
    hazard_restore_local(*sys.argv[1:])
