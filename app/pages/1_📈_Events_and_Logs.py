import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

DB_PATH = "edge_agent/rva_events.db"

st.set_page_config(page_title="Events and Logs", page_icon="📈", layout="wide")
st.title("📈 Events and Logs")

@st.cache_data(ttl=5)
def load_events():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["ts", "kind", "level", "note", "resident_id", "edge_id"])
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("select * from events order by ts desc", con)
    con.close()
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def insert_event(ts, kind, level, note, resident_id=None, edge_id=None):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "create table if not exists events(ts text, kind text, level text, note text, resident_id text, edge_id text)"
    )
    con.execute(
        "insert into events values(?,?,?,?,?,?)",
        (ts.strftime("%Y-%m-%d %H:%M:%S"), kind, level, note, resident_id, edge_id),
    )
    con.commit()
    con.close()

df = load_events()
st.dataframe(df, use_container_width=True, hide_index=True)

with st.expander("🧪 Insert demo event"):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("RESP ALERT"):
            insert_event(datetime.now(), "RESP", "ALERT", "demo br")
            st.rerun()
    with c2:
        if st.button("HR ALERT"):
            insert_event(datetime.now(), "HR", "ALERT", "demo hr")
            st.rerun()
    with c3:
        if st.button("INACTIVITY ALERT"):
            insert_event(datetime.now(), "INACTIVITY", "ALERT", "demo inactive")
            st.rerun()
