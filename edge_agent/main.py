# edge_agent/main.py
from datetime import datetime
from pathlib import Path
import time, yaml, sys, traceback

from edge_agent.signals.cam import CamSource
from edge_agent.signals.mic import MicSource
from edge_agent.signals.ppg import PPGSource
from edge_agent.utils.inference import SimpleAnomaly
from edge_agent.utils.storage import EventLogger
from edge_agent.utils.alerts import Notifier

def main():
    try:
        cfg_path = Path(__file__).parent / "configs" / "default.yaml"
        assert cfg_path.exists(), f"config not found: {cfg_path}"
        cfg = yaml.safe_load(open(cfg_path, "r", encoding="utf-8"))
        if not isinstance(cfg, dict) or "source" not in cfg:
            raise ValueError(f"invalid config: {cfg!r}")

        cam = CamSource(cfg["source"]["video"])
        mic = MicSource(cfg["source"]["audio"])
        ppg = PPGSource(cfg["source"]["ppg"])

        model = SimpleAnomaly(cfg)
        logger = EventLogger(cfg["storage"]["sqlite_path"])
        notifier = Notifier(**cfg.get("alerts", {}))

        print("[RuralVitals] Edge agent started.")
        while True:
            frame, motion = cam.read_motion()
            hr = ppg.read_hr()
            br = mic.read_brpm()
            events = model.step(motion, hr, br)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for kind, level, note in events:
                logger.log(ts, kind, level, note)
                notifier.send(kind, note)
                print(f"[{ts}] {kind}/{level}: {note}")
            time.sleep(1)
    except Exception as e:
        print("[FATAL]", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
