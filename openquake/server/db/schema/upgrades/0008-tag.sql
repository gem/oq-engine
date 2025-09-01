-- Create the new table
CREATE TABLE tag (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_string   TEXT NOT NULL,
    job_id       INTEGER REFERENCES job(id) ON DELETE SET NULL,
    is_preferred BOOLEAN NOT NULL DEFAULT 0 CHECK (is_preferred IN (0,1))
);

-- Prevent duplicate "unassigned" tags
CREATE UNIQUE INDEX unique_unassigned_tag
ON tag(tag_string)
WHERE job_id IS NULL;

-- Enforce that the same job can’t be tagged twice with the same tag
CREATE UNIQUE INDEX unique_tag_job
ON tag(tag_string, job_id);

-- Enforce that at most one job is preferred per tag
CREATE UNIQUE INDEX unique_preferred_job_per_tag
ON tag(tag_string)
WHERE is_preferred = 1
