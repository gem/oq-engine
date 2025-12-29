-- WARNING
-- This migration RESTRUCTURES the job/tag schema.
-- It preserves existing data by migrating it from the old
-- job_tag(job_id, tag, is_preferred) table into a normalized
-- schema with:
--   - tag(id, name)
--   - job_tag(job_id, tag_id, is_preferred)
-- Apply only once.

-- 1. Create new tables unconditionally
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (LENGTH(name) > 0)
);

CREATE TABLE IF NOT EXISTS job_tag_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    is_preferred INTEGER NOT NULL DEFAULT 0
        CHECK (is_preferred IN (0, 1)),
    PRIMARY KEY (job_id, tag_id),
    FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- 2. Migrate data *only if old table exists*
INSERT INTO tag (name)
SELECT DISTINCT tag
FROM job_tag
WHERE EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type='table' AND name='job_tag'
);

INSERT INTO job_tag_new (job_id, tag_id, is_preferred)
SELECT
    jt.job_id,
    t.id,
    jt.is_preferred
FROM job_tag jt
JOIN tag t ON t.name = jt.tag
WHERE EXISTS (
    SELECT 1 FROM sqlite_master
    WHERE type='table' AND name='job_tag'
);

-- 3. Drop old table if it existed
DROP TABLE IF EXISTS job_tag;

-- 4. Rename new table
ALTER TABLE job_tag_new RENAME TO job_tag;

-- 5. Recreate index
DROP INDEX IF EXISTS uq_preferred_per_tag;
CREATE UNIQUE INDEX uq_preferred_per_tag
ON job_tag(tag_id)
WHERE is_preferred = 1;
