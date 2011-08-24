/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/


-- A place to store error information in the case of a job failure.
CREATE TABLE uiapi.error_msg (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    -- Summary of the error message.
    brief VARCHAR NOT NULL,
    -- The full error message.
    detailed VARCHAR NOT NULL
) TABLESPACE uiapi_ts;

ALTER TABLE uiapi.error_msg ADD CONSTRAINT uiapi_error_msg_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE CASCADE;


-- comments:
COMMENT ON TABLE uiapi.error_msg IS 'A place to store error information in the case of a job failure.';
COMMENT ON COLUMN uiapi.error_msg.brief IS 'Summary of the error message.';
COMMENT ON COLUMN uiapi.error_msg.detailed IS 'The full error message.';


-- security:
GRANT SELECT ON uiapi.error_msg TO openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.error_msg TO oq_job_superv;
GRANT ALL ON SEQUENCE uiapi.error_msg_id_seq to GROUP openquake;
