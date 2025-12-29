-- WARNING
-- This migration RESTRUCTURES the job/tag schema.
-- It preserves existing data by migrating it from the old
-- job_tag(job_id, tag, is_preferred) table into a normalized
-- schema with:
--   - tag(id, name)
--   - job_tag(job_id, tag_id, is_preferred)
-- Apply only once.

-- 1. Remove old constraint/index if present
DROP INDEX IF EXISTS uq_preferred_per_tag;

-- 2. Rename old table (do NOT drop yet)
ALTER TABLE job_tag RENAME TO job_tag_old;

-- 3. Create normalized tag table
CREATE TABLE tag (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (LENGTH(name) > 0)
);

-- 4. Populate tag table
INSERT INTO tag (name)
SELECT DISTINCT tag
FROM job_tag_old;

-- 5. Create new join table
CREATE TABLE job_tag (
    job_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    is_preferred INTEGER NOT NULL DEFAULT 0
        CHECK (is_preferred IN (0, 1)),
    PRIMARY KEY (job_id, tag_id),
    FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- 6. Migrate associations and preferred flag
INSERT INTO job_tag (job_id, tag_id, is_preferred)
SELECT
    jto.job_id,
    t.id,
    jto.is_preferred
FROM job_tag_old AS jto
JOIN tag AS t
  ON t.name = jto.tag;

-- 7. Enforce "only one preferred job per tag"
CREATE UNIQUE INDEX uq_preferred_per_tag
ON job_tag(tag_id)
WHERE is_preferred = 1;

-- 8. Drop legacy table
DROP TABLE job_tag_old;
