import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# Database connection
@st.cache_resource
def get_engine():
    """One SQLAlchemy engine, reused across reruns."""
    return create_engine(
        f"postgresql+psycopg2://{os.environ['DASHBOARD_USER']}:{os.environ['DASHBOARD_PASSWORD']}"
        f"@postgres:5432/{os.environ['POSTGRES_DB']}"
    )

@st.cache_data(ttl=300)
def q(sql):
    """Run SQL → DataFrame. Result cached 5 min so reruns don't re-query."""
    return pd.read_sql(text(sql), get_engine())

# Page header
st.title("GitHub Archive — activity across the week")
st.caption("Does GitHub activity split into weekend-driven and always-on activity?")

# Headline
head = q("""
  WITH daily AS (
    SELECT d.category, f.date,
           CASE WHEN EXTRACT(DOW FROM f.date) IN (0,6) THEN 'weekend' ELSE 'weekday' END AS part_of_week,
           SUM(f.event_count) AS daily_events
    FROM fact_event_counts f JOIN dim_event_type d USING(event_type)
    WHERE f.is_bot = false
    GROUP BY d.category, f.date)
  SELECT category, part_of_week, ROUND(AVG(daily_events)) AS avg_events_per_day
  FROM daily GROUP BY category, part_of_week
""")
p = head.pivot(index="part_of_week", columns="category", values="avg_events_per_day")

for col, cat in zip(st.columns(len(p.columns)), p.columns):
    wknd, wkdy = p.loc["weekend", cat], p.loc["weekday", cat]
    col.metric(f"{cat} on weekends", f"{int(wknd):,}/day", f"{round(100*(wknd-wkdy)/wkdy)}%")

st.subheader("Average events per day: weekday vs weekend")
st.bar_chart(p)

# Interactive control
st.subheader("Breakdown")
view = st.radio("Break down by", ["Day of week", "Event type"], horizontal=True)

if view == "Day of week":
    d = q("""
      WITH daily AS (
        SELECT dt.category, f.date, to_char(f.date,'Dy') AS dow,
               (EXTRACT(DOW FROM f.date)::int + 6) % 7 AS dow_order,
               SUM(f.event_count) AS de
        FROM fact_event_counts f JOIN dim_event_type dt USING(event_type)
        WHERE f.is_bot = false
        GROUP BY dt.category, f.date)
      SELECT dow, dow_order, category, ROUND(AVG(de)) AS avg_events
      FROM daily GROUP BY dow, dow_order, category ORDER BY dow_order
    """)
    order = d.sort_values("dow_order")["dow"].unique()
    st.line_chart(d.pivot(index="dow", columns="category", values="avg_events").reindex(order))
else:
    d = q("""
      SELECT dt.label, SUM(f.event_count) AS events
      FROM fact_event_counts f JOIN dim_event_type dt USING(event_type)
      WHERE f.is_bot = false
      GROUP BY dt.label ORDER BY events DESC
    """)
    st.bar_chart(d.set_index("label"))

w = q("""
  SELECT min(date) AS d0, max(date) AS d1,
         count(DISTINCT date) AS n_days,
         count(DISTINCT date) FILTER (WHERE EXTRACT(DOW FROM date) IN (0,6)) AS n_weekend
  FROM fact_event_counts
""").iloc[0]
st.caption(
    f"{w.n_days} days ({w.d0} to {w.d1}), {w.n_weekend} weekend days; "
    "declared bots excluded from the human/mechanical view. "
    "Seasonal/annual variation is future work."
    )