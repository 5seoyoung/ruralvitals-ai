# edge_agent/utils/inference.py
from dataclasses import dataclass

@dataclass
class RuleThresholds:
    inactivity_sec: int = 10
    resp_brpm_low: float = 8
    resp_brpm_high: float = 28
    hr_bpm_low: float = 45
    hr_bpm_high: float = 120

class RuleModel:
    def __init__(self, cfg: dict):
        self.cfg = RuleThresholds(**cfg)
        self.motion_zero_for = 0  # 초 단위 카운터

    def step(self, motion: float, hr: float, br: float):
        evts = []

        # 무동작 카운트
        if motion <= 0.01:
            self.motion_zero_for += 1
        else:
            self.motion_zero_for = 0

        if self.motion_zero_for >= self.cfg.inactivity_sec:
            evts.append(("INACTIVITY", "ALERT", f"no motion ≥{self.cfg.inactivity_sec}s"))

        # 호흡
        if br is not None:
            if br < self.cfg.resp_brpm_low or br > self.cfg.resp_brpm_high:
                evts.append(("RESP", "ALERT", f"br≈{br:.1f} rpm out of range"))

        # 심박
        if hr is not None:
            if hr < self.cfg.hr_bpm_low or hr > self.cfg.hr_bpm_high:
                evts.append(("HR", "ALERT", f"hr≈{hr:.0f} bpm out of range"))

        # 정상 하트비트 (대시보드용 keep-alive)
        if not evts:
            evts.append(("HEARTBEAT", "INFO", "ok"))
        return evts
