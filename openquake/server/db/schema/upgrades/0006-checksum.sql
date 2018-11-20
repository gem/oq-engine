CREATE TABLE checksum(
     job_id INTEGER PRIMARY KEY REFERENCES job (id) ON DELETE CASCADE,
     hazard_checksum INTEGER NOT NULL);

CREATE INDEX hazard_checksum_id on checksum (hazard_checksum);
