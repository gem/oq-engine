CREATE TABLE job_tag (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES job(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    is_preferred INTEGER DEFAULT 0 CHECK (is_preferred IN (0, 1)),
    UNIQUE (job_id, tag)
);

-- Ensure only one preferred job per tag
CREATE UNIQUE INDEX uq_preferred_per_tag
ON job_tag(tag)
WHERE is_preferred = 1;

CREATE TRIGGER trg_preferred_requires_tag
BEFORE INSERT ON job_tag
FOR EACH ROW
WHEN NEW.is_preferred = 1 AND NEW.tag IS NULL
BEGIN
    SELECT RAISE(ABORT, 'Cannot mark job as preferred without a tag');
END;
