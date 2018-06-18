# since the ALTER TABLE command in sqlite is limited, we need this
# script to fix the NOT NULL and DEFAULT constraints on the job table
# see https://www.sqlite.org/lang_altertable.html for an explanation

output_sql = '''
CREATE TABLE output(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     oq_job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     display_name TEXT NOT NULL,
     last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ds_key TEXT NOT NULL,
     size_mb FLOAT)'''


def upgrade(conn, output_sql=output_sql):
    version, = conn.execute('PRAGMA schema_version').fetchone()
    conn.execute('PRAGMA writable_schema=ON')
    conn.execute("UPDATE sqlite_master SET sql=?"
                 "WHERE type='table' AND name='output'", (output_sql,))
    conn.execute('PRAGMA schema_version=%s' % (version + 1))
    conn.execute('PRAGMA writable_schema=OFF')
    conn.execute('PRAGMA integrity_check')
