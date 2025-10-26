# app/app.py
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import yaml

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "edge_agent" / "rva_events.db"
CFG_PATH = ROOT / "edge_agent" / "configs" / "default.yaml"

st.set_page_config(page_title="RuralVitals Edge Dashboard", page_icon="🩺", layout="wide")
st.sidebar.title("app")
st.sidebar.markdown("- 🧾 Events and Logs")

st.title("RuralVitals Edge Dashboard")
st.markdown("### 실시간 엣지 디바이스 이벤트 로그")

def read_df() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["ts", "kind", "level", "note"])
    con = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT ts, kind, level, note FROM events ORDER BY ts DESC", con)
    finally:
        con.close()
    return df

def insert_event(kind: str, level: str, note: str) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS events(ts TEXT, kind TEXT, level TEXT, note TEXT)")
        con.execute(
            "INSERT INTO events(ts, kind, level, note) VALUES(?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kind, level, note),
        )
        con.commit()
    finally:
        con.close()

# ---- 데모(시뮬레이터) 버튼 ----
with st.expander("🔧 데모(시뮬레이터)"):
    c1, c2, c3 = st.columns(3)
    if c1.button("호흡이상(ALERT) 추가"):
        insert_event("RESP", "ALERT", "br=6.0 rpm out of range")
        st.success("RESP ALERT 1건 기록됨"); st.rerun()
    if c2.button("심박이상(ALERT) 추가"):
        insert_event("HR", "ALERT", "hr=140 bpm out of range")
        st.success("HR ALERT 1건 기록됨"); st.rerun()
    if c3.button("무동작(INACTIVITY) 추가"):
        insert_event("INACTIVITY", "ALERT", "no motion ≥10s")
        st.success("INACTIVITY ALERT 1건 기록됨"); st.rerun()

df = read_df()
if df.empty:
    st.warning("아직 이벤트 데이터가 없습니다. 터미널에서 `python -m edge_agent.main`으로 엣지 에이전트를 먼저 실행하세요.")
else:
    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("총 이벤트 수", len(df))
    col2.metric("경보(ALERT) 수", int((df["level"] == "ALERT").sum()))
    col3.metric("최근 이벤트", df.iloc[0]["ts"])

    # 표
    st.dataframe(df, use_container_width=True)

    # 타임라인 그래프
    st.markdown("### Event Timeline")
    df_plot = df.copy()
    df_plot["ts"] = pd.to_datetime(df_plot["ts"])
    fig = px.scatter(
        df_plot.sort_values("ts"),
        x="ts", y="kind",
        color="level", symbol="kind",
        hover_data=["note"], template="plotly_white",
        title="Event Timeline (kind/level over time)"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---- 임계치 편집 ----
st.markdown("---")
with st.expander("⚙️ 임계치(Thresholds) 설정"):
    if not CFG_PATH.exists():
        st.error(f"설정 파일을 찾을 수 없습니다: {CFG_PATH}")
    else:
        cfg = yaml.safe_load(open(CFG_PATH, "r", encoding="utf-8")) or {}
        t = cfg.get("thresholds", {})
        c1, c2, c3, c4, c5 = st.columns(5)
        inactivity = c1.number_input("inactivity_sec", 3, 120, int(t.get("inactivity_sec", 10)))
        br_low     = c2.number_input("resp_brpm_low", 0, 60, int(t.get("resp_brpm_low", 0)))
        br_high    = c3.number_input("resp_brpm_high", 10, 120, int(t.get("resp_brpm_high", 100)))
        hr_low     = c4.number_input("hr_bpm_low", 30, 100, int(t.get("hr_bpm_low", 45)))
        hr_high    = c5.number_input("hr_bpm_high", 80, 200, int(t.get("hr_bpm_high", 120)))
        if st.button("설정 저장"):
            cfg["thresholds"] = {
                "inactivity_sec": int(inactivity),
                "resp_brpm_low": int(br_low),
                "resp_brpm_high": int(br_high),
                "hr_bpm_low": int(hr_low),
                "hr_bpm_high": int(hr_high),
            }
            with open(CFG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
            st.success("저장되었습니다. 엣지 에이전트 재시작 시 적용됩니다.")

# ---- CSV 다운로드 ----
if not df.empty:
    st.download_button(
        "⬇️ 이벤트 로그 CSV 다운로드",
        df.to_csv(index=False).encode("utf-8"),
        "ruralvitals_events.csv",
        "text/csv"
    )

st.caption("RuralVitals Edge AI Monitoring System © 2025 MediX / Seoyoung Oh")
