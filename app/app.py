import os
import sqlite3
from datetime import datetime
from typing import List

import pandas as pd
import streamlit as st
import altair as alt

DB_PATH = "edge_agent/rva_events.db"
REG_PATH = "data/resident_registry.csv"

st.set_page_config(
    page_title="RuralVitals — 충북 농촌형 엣지 돌봄 대시보드",
    page_icon="🌾",
    layout="wide",
)

# -----------------------------
# Regions
# -----------------------------
CHUNGBUK_REGIONS: List[str] = [
    "전체",
    # 시(3)
    "제천시", "청주시", "충주시",
    # 군(8)
    "괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "증평군", "진천군",
]

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=5)
def load_events(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    try:
        # 현재 테이블 컬럼 확인
        cols = {row[1] for row in con.execute("PRAGMA table_info(events)")}
        # 필수 컬럼 구성 (없으면 즉석 기본값으로 alias)
        sel = ["ts", "kind", "level", "note"]
        if "resident_id" in cols:
            sel.append("resident_id")
        else:
            sel.append("'UNSET' AS resident_id")
        if "edge_id" in cols:
            sel.append("edge_id")
        else:
            sel.append("'edge-1' AS edge_id")

        sql = f"SELECT {', '.join(sel)} FROM events ORDER BY ts DESC"
        df = pd.read_sql(sql, con)
        df["ts"] = pd.to_datetime(df["ts"])
        return df
    finally:
        con.close()
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    for col in ["resident_id", "edge_id", "kind", "level", "note"]:
        if col not in df.columns:
            df[col] = None
    return df

def ensure_registry_template(events: pd.DataFrame) -> pd.DataFrame:
    """등록 파일이 없으면 이벤트의 resident_id로 템플릿 생성."""
    os.makedirs(os.path.dirname(REG_PATH), exist_ok=True)
    if os.path.exists(REG_PATH):
        reg = pd.read_csv(REG_PATH, dtype=str).fillna("미지정")
    else:
        ids = sorted(set(events["resident_id"].dropna())) or ["CB-001", "CB-002"]
        reg = pd.DataFrame({
            "resident_id": ids,
            "name": [f"어르신{str(i+1).zfill(2)}" for i in range(len(ids))],
            "county": ["미지정"] * len(ids),
        })
        reg.to_csv(REG_PATH, index=False, encoding="utf-8-sig")
    # 보정
    for col in ["resident_id", "name", "county"]:
        if col not in reg.columns:
            reg[col] = "미지정"
    return reg

def insert_event(ts: datetime, kind: str, level: str, note: str, resident_id: str | None, edge_id: str | None):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        create table if not exists events(
            ts text,
            kind text,
            level text,
            note text,
            resident_id text,
            edge_id text
        )
        """
    )
    cur.execute(
        "insert into events(ts,kind,level,note,resident_id,edge_id) values(?,?,?,?,?,?)",
        (ts.strftime("%Y-%m-%d %H:%M:%S"), kind, level, note, resident_id, edge_id),
    )
    con.commit()
    con.close()

def heat_color(n: int) -> str:
    if n >= 10:   # 고위험
        return "#ffe5e5"
    if n >= 5:    # 주의
        return "#fff5e6"
    return "#eef9f0"  # 양호

def classify_status(last_row: pd.Series | None) -> str:
    """
    최근 이벤트 기준 간단 상태 분류:
      - RESP/HR ALERT -> critical
      - INACTIVITY ALERT -> warning
      - 그 외 -> normal
    """
    if last_row is None or pd.isna(last_row.get("kind")):
        return "normal"
    if last_row.get("level") == "ALERT":
        k = (last_row.get("kind") or "").upper()
        if k in ("RESP", "HR"):
            return "critical"
        if k in ("INACTIVITY",):
            return "warning"
    return "normal"

# -----------------------------
# LOAD
# -----------------------------
events = load_events(DB_PATH)
reg = ensure_registry_template(events)

now = pd.Timestamp.now()
cut_24h = now - pd.Timedelta(hours=24)
online_cut = now - pd.Timedelta(seconds=90)

hb = events[events["note"] == "edge alive"].copy()
hb = hb.sort_values(["resident_id", "ts"], ascending=[True, False])
online_ids = set(hb.groupby("resident_id").head(1).loc[lambda d: d["ts"] >= online_cut, "resident_id"])

# 지역 필터 UI (React 컨셉과 동일한 경험)
st.title("RuralVitals — 충북 농촌형 엣지 돌봄 대시보드")
st.caption("비착용 · 오프라인 추론 · 저비용 다인 커버리지")

region = st.segmented_control("📍 지역 선택", options=CHUNGBUK_REGIONS, default="전체")
reg_view = reg.copy()
if region != "전체":
    reg_view = reg_view[reg_view["county"] == region]

# KPI
total_alerts = int((events["level"] == "ALERT").sum())
last_ts = events["ts"].max() if not events.empty else None

colA, colB, colC = st.columns(3)
colA.metric("모니터링 대상자 수", len(reg_view))
colB.metric("총 ALERT(전체)", total_alerts)
colC.metric("최근 이벤트 시각", last_ts.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(last_ts) else "-")

# -----------------------------
# 대상자 현황(카드형) — 지역 필터 반영
# -----------------------------
st.subheader("대상자 현황(다인)")
if len(reg_view) == 0:
    st.info("해당 지역에 등록된 대상자가 없습니다. (data/resident_registry.csv에서 county를 설정하세요)")
else:
    # 대상자별 최신 이벤트 머지
    latest = (
        events.sort_values("ts", ascending=False)
        .drop_duplicates(subset=["resident_id"], keep="first")
        .rename(columns={"ts": "last_ts"})
    )
    merged = reg_view.merge(latest[["resident_id", "kind", "level", "note", "last_ts"]], on="resident_id", how="left")

    # 간단 KPI 계산(필터된 집합 기준)
    statuses = merged.apply(lambda r: classify_status(r), axis=1)
    critical_cnt = int((statuses == "critical").sum())
    warning_cnt = int((statuses == "warning").sum())
    normal_cnt = int((statuses == "normal").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("긴급 알림(critical)", critical_cnt)
    k2.metric("주의 필요(warning)", warning_cnt)
    k3.metric("정상(normal)", normal_cnt)
    k4.metric("필터 적용 대상자", len(merged))

    # 카드 그리드
    ncols = 2 if st.session_state.get("wide_cards", True) else 1
    for i, row in merged.reset_index(drop=True).iterrows():
        if i % ncols == 0:
            cols = st.columns(ncols)
        idx = i % ncols
        status = classify_status(row)
        dot = {"critical": "🔴", "warning": "🟡", "normal": "🟢"}.get(status, "⚪️")
        badge = f"<span style='background:#e9f0ff;color:#315efb;padding:2px 8px;border-radius:999px;font-size:12px'>{row['county']}</span>"

        with cols[idx]:
            st.markdown(
                f"""
                <div style="
                    border:2px solid {'#ffb3b3' if status=='critical' else ('#ffe199' if status=='warning' else '#cde8cf')};
                    background:{'#fff7f7' if status=='critical' else ('#fffaf0' if status=='warning' else '#f5fff7')};
                    padding:14px;border-radius:14px;margin-bottom:10px;">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <div style="font-weight:700;font-size:16px">{dot} {row.get('name','어르신')} <span style="color:#999">({row['resident_id']})</span></div>
                    <div>{badge}</div>
                  </div>
                  <div style="color:#666;margin-top:6px">
                    최근: {row['last_ts'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('last_ts')) else '-'} /
                    {str(row.get('kind') or '-')} {str(row.get('level') or '')}
                  </div>
                  <div style="color:#444;margin-top:4px">{str(row.get('note') or '')}</div>
                  <div style="margin-top:6px;font-size:12px;color:{'#b30000' if status=='critical' else ('#8a6a00' if status=='warning' else '#2d6a30')}">
                    상태: <b>{'위험' if status=='critical' else ('주의' if status=='warning' else '정상')}</b>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# -----------------------------
# 충북 시·군 현황 카드 (최근 24h) — 전체 관점
# -----------------------------
st.subheader("충청북도 시·군 현황(최근 24시간)")
merge = events.merge(reg, on="resident_id", how="left")
merge["county"] = merge["county"].fillna("미지정")
recent = merge[merge["ts"] >= cut_24h]
agg = recent.groupby("county").agg(
    alerts=("level", lambda s: int((s == "ALERT").sum())),
    residents=("resident_id", "nunique"),
    latest=("ts", "max"),
).reset_index()

if agg.empty:
    st.info("최근 24시간 데이터가 없습니다. (아래 데모 이벤트 주입으로 테스트하세요)")
else:
    counties = list(agg.sort_values("alerts", ascending=False)["county"])
    ncols = 4
    rows = (len(counties) + ncols - 1) // ncols
    for r in range(rows):
        cols = st.columns(ncols)
        for c in range(ncols):
            idx = r * ncols + c
            if idx >= len(counties):
                continue
            name = counties[idx]
            row = agg[agg["county"] == name].iloc[0]
            with cols[c]:
                bg = heat_color(row["alerts"])
                st.markdown(
                    f"""
                    <div style="background:{bg};padding:14px;border-radius:16px;border:1px solid #e6e6e6">
                      <div style="font-weight:700;font-size:18px">{name}</div>
                      <div style="margin-top:6px">최근24h ALERT: <b>{row['alerts']}</b></div>
                      <div>모니터링 대상자: {row['residents']}명</div>
                      <div style="color:#666">최근: {row['latest'].strftime('%m-%d %H:%M') if pd.notna(row['latest']) else '-'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# -----------------------------
# 통합 알림 피드
# -----------------------------
st.subheader("통합 알림 피드")
feed_cols = ["ts", "resident_id", "kind", "level", "note"]
feed = events.loc[:, [c for c in feed_cols if c in events.columns]].copy()
if region != "전체":
    feed = feed.merge(reg_view[["resident_id"]], on="resident_id", how="inner")
st.dataframe(feed.head(20), use_container_width=True, hide_index=True)

# -----------------------------
# Event Timeline
# -----------------------------
st.caption("Event Timeline (kind/level over time)")
if not events.empty:
    ev = events.copy()
    if region != "전체":
        ev = ev.merge(reg_view[["resident_id"]], on="resident_id", how="inner")
    ev["level_kind"] = ev["level"].fillna("") + ", " + ev["kind"].fillna("")
    ch = alt.Chart(ev.tail(800)).mark_point().encode(
        x=alt.X("ts:T", title="ts"),
        y=alt.Y("kind:N"),
        color=alt.Color("level_kind:N", legend=alt.Legend(title="level,kind")),
        tooltip=["ts", "resident_id", "level", "kind", "note"],
    ).properties(height=220, width="container")
    st.altair_chart(ch, use_container_width=True)
else:
    st.info("표시할 이벤트가 없습니다.")

# -----------------------------
# 데모(이벤트 주입) — 버튼 고침은 st.rerun
# -----------------------------
with st.expander("🧪 데모(이벤트 주입)"):
    rid = st.selectbox("대상자 선택", reg["resident_id"].tolist() or ["CB-001"])
    edge_id = st.text_input("엣지 디바이스 ID", value="edge-01")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("호흡이상(ALERT) 추가"):
            insert_event(datetime.now(), "RESP", "ALERT", "br≈0 rpm out of range", rid, edge_id)
            st.toast("호흡이상(ALERT) 등록", icon="✅")
            st.rerun()
    with c2:
        if st.button("심박이상(ALERT) 추가"):
            insert_event(datetime.now(), "HR", "ALERT", "hr≈140 bpm out of range", rid, edge_id)
            st.toast("심박이상(ALERT) 등록", icon="✅")
            st.rerun()
    with c3:
        if st.button("무움직임(INACTIVITY) 추가"):
            insert_event(datetime.now(), "INACTIVITY", "ALERT", "no motion ≥10s", rid, edge_id)
            st.toast("무움직임(INACTIVITY) 등록", icon="✅")
            st.rerun()

st.markdown("<hr/>", unsafe_allow_html=True)
st.caption("RuralVitals Edge AI Monitoring System © 2025 Medix / Seoyoung Oh")
