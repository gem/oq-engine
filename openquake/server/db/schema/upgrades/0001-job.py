# since the ALTER TABLE command in sqlite is limited, we need this
# script to fix the NOT NULL and DEFAULT constraints on the job table
# see https://www.sqlite.org/lang_altertable.html for an explanation

job_sql = '''CREATE TABLE job(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     description TEXT NOT NULL,
     user_name TEXT NOT NULL,
     calculation_mode TEXT NOT NULL,
     hazard_calculation_id INTEGER REFERENCES job (id) ON DELETE CASCADE,
     status TEXT NOT NULL DEFAULT 'created',
     is_running BOOL NOT NULL DEFAULT 1,
     start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     stop_time TIMESTAMP,
     relevant BOOL NOT NULL DEFAULT 1,
     ds_calc_dir TEXT NOT NULL)'''


def upgrade(conn, job_sql=job_sql):
    version, = conn.execute('PRAGMA schema_version').fetchone()
    conn.execute('PRAGMA writable_schema=ON')
    conn.execute("UPDATE sqlite_master SET sql=?"
                 "WHERE type='table' AND name='job'", (job_sql,))
    conn.execute('PRAGMA schema_version=%s' % (version + 1))
    conn.execute('PRAGMA writable_schema=OFF')
    conn.execute('PRAGMA integrity_check')
