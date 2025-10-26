# edge_agent/utils/inference.py
class SimpleAnomaly:
    def __init__(self, cfg: dict):
        t = cfg["thresholds"]
        self.inactivity = int(t["inactivity_sec"])
        self.hr_low, self.hr_high = float(t["hr_bpm_low"]), float(t["hr_bpm_high"])
        self.br_low, self.br_high = float(t["resp_brpm_low"]), float(t["resp_brpm_high"])
        self._still = 0

    def step(self, motion_score: float, hr_bpm: float, br_bpm: float):
        ev = []
        if motion_score < 0.01:
            self._still += 1
        else:
            self._still = 0
        if self._still >= self.inactivity:
            ev.append(("INACTIVITY", "ALERT", f"no motion ≥{self.inactivity}s"))
            self._still = 0

        if hr_bpm < self.hr_low or hr_bpm > self.hr_high:
            ev.append(("HR", "ALERT", f"hr={hr_bpm:.1f} bpm out of range"))
        if br_bpm < self.br_low or br_bpm > self.br_high:
            ev.append(("RESP", "ALERT", f"br={br_bpm:.1f} rpm out of range"))
        return ev
