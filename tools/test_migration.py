#!/usr/bin/env python

import re
import subprocess

db_admin_user = 'postgres'
original_db = 'original'

def psql(*args):
    subprocess.check_call(['psql', '-U', db_admin_user] + list(args))

def load(path):
    subprocess.check_call('zcat %s | psql -U %s -d %s' % (
            path, db_admin_user, original_db), shell=True)

def pg_dump(to_file):
    pg = subprocess.Popen(['pg_dump', '--schema-only', '-U', db_admin_user,
                           original_db], stdout=subprocess.PIPE)

    comments = []
    columns = []
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

            # move comments to the end
            if line.startswith('COMMENT '):
                comments.append(line)
                continue

            if line.startswith('CREATE TABLE'):
                in_table = True;
                columns = []

            out.write(line)

        # write out comments sorted
        for comment in sorted(comments):
            out.write(comment)


# DB from create_oq_schema
psql('-c', "DROP DATABASE IF EXISTS %s" % original_db)
psql('-c', "CREATE DATABASE %s" % original_db)

subprocess.check_call(['bin/create_oq_schema', '--yes',
                       '--db-name=%s' % original_db,
                       '--db-user=%s' % db_admin_user,
                       '--schema-path=%s' % 'openquake/db/schema'])

pg_dump('/tmp/fresh.sql')

# DB from dbmaint.py
psql('-c', "DROP DATABASE IF EXISTS %s" % original_db)
psql('-c', "CREATE DATABASE %s" % original_db)
load('tools/test_migration_base.sql.gz')

subprocess.check_call(['tools/dbmaint.py', '--db', original_db,
                       '-U', db_admin_user])

pg_dump('/tmp/after.sql')

subprocess.call('diff -u /tmp/fresh.sql /tmp/after.sql | less -F', shell=True)
