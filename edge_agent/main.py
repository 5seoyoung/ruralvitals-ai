# edge_agent/main.py
import time, sys, traceback, yaml
from datetime import datetime
from edge_agent.signals.cam import CamSource
from edge_agent.signals.mic import MicSource
from edge_agent.signals.ppg import PPGSource
from edge_agent.utils.inference import RuleModel
from edge_agent.utils.storage import EventLogger
from edge_agent.utils.alerts import Notifier

CFG_PATH = "edge_agent/configs/default.yaml"

def load_cfg(path=CFG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    cfg = load_cfg()
    cam = CamSource(cfg["source"]["video"])
    mic = MicSource(cfg["source"]["audio"])
    ppg = PPGSource(cfg["source"]["ppg_csv"])
    model = RuleModel(cfg["thresholds"])
    logger = EventLogger(cfg["storage"]["sqlite_path"])
    notifier = Notifier(**cfg.get("alerts", {}))
    resident = cfg.get("resident", {"resident_id":"CB-001", "name":"A 어르신"})

    print("[RuralVitals] Edge agent started.")

    try:
        while True:
            frame, motion = cam.read_motion()
            hr = ppg.read_hr()
            br = mic.read_brpm()
            events = model.step(motion, hr, br)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # HEARTBEAT
            logger.log(ts, resident["resident_id"], "HEARTBEAT", "INFO", "ok")

            for kind, level, note in events:
                logger.log(ts, resident["resident_id"], kind, level, note)
                notifier.send(kind, note)

            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("[FATAL]", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
