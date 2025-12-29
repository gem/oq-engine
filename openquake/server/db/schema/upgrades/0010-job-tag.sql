DROP INDEX IF EXISTS uq_preferred_per_tag;
DROP TABLE IF EXISTS job_tag;

CREATE TABLE tag (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (LENGTH(name) > 0)
);

CREATE TABLE job_tag (
    job_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    is_preferred INTEGER NOT NULL DEFAULT 0
        CHECK (is_preferred IN (0, 1)),

    PRIMARY KEY (job_id, tag_id),

    FOREIGN KEY (job_id) REFERENCES job(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX uq_preferred_per_tag
ON job_tag(tag_id)
WHERE is_preferred = 1;
