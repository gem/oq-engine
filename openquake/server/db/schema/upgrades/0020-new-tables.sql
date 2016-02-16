CREATE TABLE job(
     id SERIAL PRIMARY KEY,
     description TEXT NOT NULL,
     user_name TEXT NOT NULL,
     calculation_mode TEXT NOT NULL,
     hazard_calculation_id INTEGER REFERENCES job (id) ON DELETE CASCADE,
     status TEXT NOT NULL DEFAULT 'created',
     is_running BOOL NOT NULL DEFAULT false,
     start_time TIMESTAMP NOT NULL DEFAULT timezone('UTC', now()),
     stop_time TIMESTAMP,
     relevant BOOL DEFAULT true,
     ds_calc_dir TEXT NOT NULL);
GRANT ALL ON job TO oq_job_init;
GRANT USAGE ON job_id_seq TO oq_job_init;


CREATE TABLE log(
     id SERIAL PRIMARY KEY,
     job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     timestamp TIMESTAMP NOT NULL,
     level TEXT NOT NULL,
     process TEXT NOT NULL,
     message TEXT NOT NULL);   
GRANT ALL ON log TO oq_job_init;
GRANT USAGE ON log_id_seq TO oq_job_init;


CREATE TABLE output(
     id SERIAL PRIMARY KEY,     
     oq_job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     display_name TEXT NOT NULL,
     last_update TIMESTAMP NOT NULL DEFAULT timezone('UTC', now()),
     ds_key TEXT NOT NULL);
GRANT ALL ON output TO oq_job_init;
GRANT USAGE ON output_id_seq TO oq_job_init;


CREATE TABLE performance(
     id SERIAL PRIMARY KEY,
     job_id INTEGER NOT NULL REFERENCES job (id) ON DELETE CASCADE,
     operation TEXT NOT NULL,
     time_sec FLOAT NOT NULL,
     memory_mb FLOAT NOT NULL,
     counts INTEGER NOT NULL);
GRANT ALL ON performance TO oq_job_init;
GRANT USAGE ON performance_id_seq TO oq_job_init;
