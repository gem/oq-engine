CREATE TABLE job(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     description TEXT NOT NULL,
     user_name TEXT NOT NULL,
     calculation_mode TEXT NOT NULL,
     hazard_calculation_id INTEGER REFERENCES job (id) ON DELETE CASCADE,
     status TEXT NOT NULL DEFAULT 'created',
     is_running BOOL NOT NULL DEFAULT false,
     start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     stop_time TIMESTAMP,
     relevant BOOL DEFAULT true,
     ds_calc_dir TEXT NOT NULL);

CREATE TABLE log(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     timestamp TIMESTAMP NOT NULL,
     level TEXT NOT NULL,
     process TEXT NOT NULL,
     message TEXT NOT NULL);

CREATE TABLE output(
     id INTEGER PRIMARY KEY AUTOINCREMENT,     
     oq_job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     display_name TEXT NOT NULL,
     last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     ds_key TEXT NOT NULL);

CREATE TABLE performance(
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     operation TEXT NOT NULL,
     time_sec FLOAT NOT NULL,
     memory_mb FLOAT NOT NULL,
     counts INTEGER NOT NULL);
