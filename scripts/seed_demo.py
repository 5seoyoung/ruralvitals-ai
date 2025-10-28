# scripts/seed_demo.py
import argparse, sqlite3, random
from datetime import datetime, timedelta

REGIONS = [
    "제천시","청주시","충주시",
    "괴산군","단양군","보은군","영동군","옥천군","음성군","증평군","진천군"
]
NAMES = ["김영희","박철수","이순자","최민호","정미숙","강동욱","윤서연","한지훈","조민정","송태현","배수진",
         "오은정","장민지","임하늘","권도현","서지우","배도윤","김도아","이지후","정하린"]

def ensure_schema(con):
    cur = con.cursor()
    # residents
    cur.execute("""
    CREATE TABLE IF NOT EXISTS residents(
        resident_id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        region TEXT,
        room TEXT
    );
    """)
    # heartbeats
    cur.execute("""
    CREATE TABLE IF NOT EXISTS heartbeats(
        ts TEXT,
        resident_id TEXT,
        edge_id TEXT,
        status TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hb_ts ON heartbeats(ts);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hb_res ON heartbeats(resident_id);")

    # events (없던 컬럼 자동 보강)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events(
        ts TEXT,
        kind TEXT,
        level TEXT,
        note TEXT
    );
    """)
    cols = {r[1] for r in cur.execute("PRAGMA table_info(events);").fetchall()}
    if "resident_id" not in cols:
        cur.execute("ALTER TABLE events ADD COLUMN resident_id TEXT;")
    if "edge_id" not in cols:
        cur.execute("ALTER TABLE events ADD COLUMN edge_id TEXT;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ev_ts ON events(ts);")
    con.commit()

def gen_resident_id(i): return f"CB-{i:03d}"
def gen_room(i):
    wing = "ABCD"[(i//100) % 4]
    return f"{wing}-{100+(i%100):03d}"

def seed_residents(con, count):
    cur = con.cursor()
    existing = {r[0] for r in cur.execute("SELECT resident_id FROM residents").fetchall()}
    new_rows = []
    for i in range(1, count+1):
        rid = gen_resident_id(i)
        if rid in existing: continue
        new_rows.append((
            rid, random.choice(NAMES), random.randint(74, 89),
            random.choice(REGIONS), gen_room(i)
        ))
    if new_rows:
        cur.executemany("INSERT INTO residents(resident_id,name,age,region,room) VALUES(?,?,?,?,?)", new_rows)
        con.commit()
    return count

def seed_streams(con, days, hb_interval_sec, residents, edge_nodes):
    cur = con.cursor()
    now = datetime.now()
    start = now - timedelta(days=days)
    edges = [f"edge-{i:02d}" for i in range(1, edge_nodes+1)]

    hb_rows, ev_rows = [], []
    baselines = {gen_resident_id(i):
                    (random.randint(66,78), random.randint(12,18), random.choice(edges))
                 for i in range(1,residents+1)}

    t = start
    while t <= now:
        ts = t.strftime("%F %T")
        for i in range(1, residents+1):
            rid = gen_resident_id(i)
            hr, br, edge = baselines[rid]

            # heartbeat
            status = "ONLINE" if random.random() > 0.01 else "OFFLINE"
            hb_rows.append((ts, rid, edge, status))

            # RESP 이벤트
            p = random.random()
            if p < 0.003:
                ev_rows.append((ts, "RESP", "ALERT", f"br={random.randint(30,40)} rpm out of range", rid, edge))
            elif p < 0.010:
                ev_rows.append((ts, "RESP", "WARN",  f"br={random.randint(24,28)} rpm high", rid, edge))

            # HR 이벤트
            p2 = random.random()
            if p2 < 0.002:
                ev_rows.append((ts, "HR", "ALERT", f"hr={random.randint(120,140)} bpm out of range", rid, edge))
            elif p2 < 0.006:
                ev_rows.append((ts, "HR", "WARN",  f"hr={random.randint(95,110)} bpm high", rid, edge))

            # 무활동
            if random.random() < 0.0015:
                sev = "ALERT" if random.random() < 0.6 else "WARN"
                ev_rows.append((ts, "INACTIVITY", sev, f"no motion ≥{random.choice([10,20,30])}s", rid, edge))
        t += timedelta(seconds=hb_interval_sec)

    cur.executemany("INSERT INTO heartbeats(ts,resident_id,edge_id,status) VALUES(?,?,?,?)", hb_rows)
    cur.executemany("INSERT INTO events(ts,kind,level,note,resident_id,edge_id) VALUES(?,?,?,?,?,?)", ev_rows)
    con.commit()
    return len(hb_rows), len(ev_rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="edge_agent/rva_events.db")
    ap.add_argument("--residents", type=int, default=12)
    ap.add_argument("--edges", type=int, default=3)
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--hb-interval", type=int, default=120)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    ensure_schema(con)
    if args.reset:
        cur = con.cursor()
        cur.execute("DELETE FROM heartbeats;")
        cur.execute("DELETE FROM events;")
        con.commit()

    seed_residents(con, args.residents)
    hb, ev = seed_streams(con, args.days, args.hb_interval, args.residents, args.edges)

    cur = con.cursor()
    res_n = cur.execute("SELECT COUNT(*) FROM residents").fetchone()[0]
    hb_n = cur.execute("SELECT COUNT(*) FROM heartbeats").fetchone()[0]
    ev_n = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"[OK] residents={res_n}, heartbeats={hb_n}, events={ev_n}")
    for row in cur.execute("SELECT ts,kind,level,note,resident_id FROM events ORDER BY ts DESC LIMIT 5"):
        print("  -", row)
    con.close()

if __name__ == "__main__":
    main()


