CREATE TABLE IF NOT EXISTS fact_event_counts (
    hour_ts     timestamptz NOT NULL,
    event_type  text        NOT NULL,
    is_bot      boolean     NOT NULL,
    event_count bigint      NOT NULL,
    date        date        NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_event_counts_date ON fact_event_counts (date);

CREATE TABLE IF NOT EXISTS dim_event_type (
    event_type TEXT PRIMARY KEY,
    category   TEXT NOT NULL,
    label      TEXT
);

INSERT INTO dim_event_type (event_type, category, label) VALUES
  ('PushEvent',                     'mechanical',   'Push'),
  ('CreateEvent',                   'mechanical',   'Create (branch/tag/repo)'),
  ('DeleteEvent',                   'mechanical',   'Delete (branch/tag)'),
  ('PullRequestEvent',              'human-social', 'Pull Request'),
  ('PullRequestReviewEvent',        'human-social', 'PR Review'),
  ('PullRequestReviewCommentEvent', 'human-social', 'PR Review Comment'),
  ('IssuesEvent',                   'human-social', 'Issue'),
  ('IssueCommentEvent',             'human-social', 'Issue Comment'),
  ('CommitCommentEvent',            'human-social', 'Commit Comment'),
  ('WatchEvent',                    'human-social', 'Star'),
  ('ForkEvent',                     'human-social', 'Fork'),
  ('ReleaseEvent',                  'human-social', 'Release'),
  ('PublicEvent',                   'human-social', 'Made Public'),
  ('MemberEvent',                   'human-social', 'Member Added'),
  ('GollumEvent',                   'human-social', 'Wiki Edit')
ON CONFLICT (event_type) DO NOTHING;