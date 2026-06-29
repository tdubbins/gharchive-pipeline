CREATE TABLE IF NOT EXISTS fact_event_counts (
    hour_ts     timestamptz NOT NULL,
    event_type  text        NOT NULL,
    is_bot      boolean     NOT NULL,
    event_count bigint      NOT NULL,
    date        date        NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_event_counts_date ON fact_event_counts (date);