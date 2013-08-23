#!/usr/bin/env python

import os
import re
import subprocess
import sys

db_admin_user = 'postgres'
original_db = 'original'


def info(message):
    print message


def quiet_check_call(*args, **kwargs):
    try:
        with open('/tmp/subprocess.out', 'w') as out:
            subprocess.check_call(*args,
                                   stderr=subprocess.STDOUT,
                                   stdout=out,
                                   **kwargs)
    except:
        with open('/tmp/subprocess.out') as fh:
            print fh.read()

        raise
    finally:
        os.unlink('/tmp/subprocess.out')


def psql(*args):
    quiet_check_call(['psql', '-U', db_admin_user] + list(args))


def load(path):
    quiet_check_call('zcat %s | psql -U %s -d %s' % (
            path, db_admin_user, original_db), shell=True)


def pg_dump(to_file):
    pg = subprocess.Popen(['pg_dump', '--schema-only', '-U', db_admin_user,
                           '--exclude-schema', 'public',
                           original_db], stdout=subprocess.PIPE)

    comments = []
    columns = []
    alters = []
    alter_start = None
    in_table = False

    with open(to_file, 'w') as out:
        for line in pg.stdout:
            # skip SQL comments and blank lines
            if line.startswith('--') or line == '\n':
                continue

            # normalize conditions (for some reason pg_dump dumps them
            # differently before and after an upgrade)
            if line.startswith('    CONSTRAINT'):
                line = re.sub(r"\('(\w+)'::character varying\)::text",
                              r"'\1'::character varying", line)
                line = re.sub(r"ANY \(\(ARRAY\[(.*?)\]\)::text\[\]\)",
                              r"ANY (ARRAY[\1])", line)

            # reorder table columns
            if in_table:
                if line == ');\n':
                    # table finished
                    in_table = False
                else:
                    # accumulate table lines
                    line = re.sub(r",\n", r"\n", line)
                    columns.append(line)
                    continue

                # write table lines sorted
                for column in sorted(columns):
                    out.write(column)

            # ignore the name of UNIQUE keys until we start naming
            # them explicitly
            if alter_start:
                if re.match(r"^    ADD CONSTRAINT \w+_key UNIQUE ", line):
                    line = re.sub(r"    ADD CONSTRAINT (\w+)_key UNIQUE ",
                                  r"    ADD CONSTRAINT <elided>_key UNIQUE ",
                                  line)
                    alters.append(alter_start + line)
                    alter_start = None
                    continue
                else:
                    line = alter_start + line
                    alter_start = None
            elif line.startswith('ALTER TABLE ONLY '):
                alter_start = line
                continue

            # move comments to the end
            if line.startswith('COMMENT '):
                comments.append(line)
                continue

            if line.startswith('CREATE TABLE'):
                in_table = True
                columns = []

            out.write(line)

        # write out alters sorted
        for alter in sorted(alters):
            out.write(alter)

        # write out comments sorted
        for comment in sorted(comments):
            out.write(comment)


# DB from oq_create_db
info('Creating a fresh database using oq_create_db...')

psql('-c', "DROP DATABASE IF EXISTS %s" % original_db)
psql('-c', "CREATE DATABASE %s" % original_db)

quiet_check_call(['bin/oq_create_db', '--yes', '--no-tab-spaces',
                  '--db-name=%s' % original_db,
                  '--db-user=%s' % db_admin_user,
                  '--schema-path=%s' % 'openquake/db/schema'])

info('Dumping the database...')
pg_dump('/tmp/fresh.sql')

# DB from dbmaint.py
info('Loading database from old dump...')
psql('-c', "DROP DATABASE IF EXISTS %s" % original_db)
psql('-c', "CREATE DATABASE %s" % original_db)
load('tools/test_migration_base.sql.gz')

info('Upgrading database using dbmaint...')
quiet_check_call(['tools/dbmaint.py', '--db', original_db,
                  '-U', db_admin_user])

info('Dumping the database...')
pg_dump('/tmp/after.sql')

info('Comparing new and upgraded version...')
res = subprocess.call(['diff', '-u', '/tmp/fresh.sql', '/tmp/after.sql'])

sys.exit(res)
