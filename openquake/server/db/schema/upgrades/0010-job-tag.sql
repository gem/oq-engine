-- WARNING
-- This migration RESTRUCTURES the job/tag schema.
-- It preserves existing data by migrating it from the old
-- job_tag(job_id, tag, is_preferred) table into a normalized
-- schema with:
--   - tag(id, name)
--   - job_tag(job_id, tag_id, is_preferred)
-- Apply only once.

-- Remove old constraint/index if present
DROP INDEX IF EXISTS uq_preferred_per_tag;

-- Rename old table (do NOT drop yet)
ALTER TABLE job_tag RENAME TO job_tag_old;

-- Create new tables
CREATE TABLE tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE CHECK (LENGTH(name) > 0)
);

CREATE TABLE job_tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    is_preferred INTEGER NOT NULL DEFAULT 0
        CHECK (is_preferred IN (0, 1)),
    UNIQUE (job_id, tag_id),
    FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- Migrate tag values
INSERT INTO tag (name)
SELECT DISTINCT tag
FROM job_tag_old;

-- Migrate job-tag relations
INSERT INTO job_tag (job_id, tag_id, is_preferred)
SELECT
    jto.job_id,
    t.id,
    jto.is_preferred
FROM job_tag_old AS jto
JOIN tag AS t
  ON t.name = jto.tag;

-- Drop old table
DROP TABLE job_tag_old;

-- Recreate constraint, consistent with the new schema
CREATE UNIQUE INDEX uq_preferred_per_tag
ON job_tag(tag_id)
WHERE is_preferred = 1;
