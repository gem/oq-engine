/*

    Copyright (c) 2010-2011, GEM Foundation.

    OpenQuake database is made available under the Open Database License:
    http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual
    contents of the database are licensed under the Database Contents License:
    http://opendatacommons.org/licenses/dbcl/1.0/

*/

-- Persistent storage for job log messages
CREATE TABLE uiapi.log_msg (
    id SERIAL PRIMARY KEY,
    oq_job_id INTEGER NOT NULL,
    -- Short log message summary.
    brief VARCHAR NOT NULL,
    -- Full log message.
    detailed VARCHAR NOT NULL,
    log_level VARCHAR NOT NULL CONSTRAINT log_msg_levels
        CHECK(log_level IN ('debug', 'info', 'warning', 'error', 'critical',
            'fatal')),
    log_date timestamp without time zone
        DEFAULT timezone('UTC'::text, now()) NOT NULL
) TABLESPACE uiapi_ts;

ALTER TABLE uiapi.log_msg ADD CONSTRAINT uiapi_log_msg_oq_job_fk
FOREIGN KEY (oq_job_id) REFERENCES uiapi.oq_job(id) ON DELETE RESTRICT;


-- comments
COMMENT ON TABLE uiapi.log_msg IS 'Persistent storage for job log messages.';
COMMENT ON COLUMN uiapi.log_msg.brief IS 'Short log message summary.';
COMMENT ON COLUMN uiapi.log_msg.detailed IS 'Full log message.';


-- security
GRANT ALL ON SEQUENCE uiapi.log_msg_id_seq to GROUP openquake;

GRANT SELECT ON uiapi.log_msg TO GROUP openquake;
GRANT SELECT,INSERT,UPDATE,DELETE ON uiapi.log_msg to oq_uiapi_writer;
