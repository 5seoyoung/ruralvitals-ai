# edge_agent/signals/mic.py
import time, math

class MicSource:
    def __init__(self, path: str):
        self.t0 = time.time()

    def read_brpm(self) -> float:
        # 데모용: 12~16 rpm 사이 완만 변동 (실장비 없이 안정적 데모)
        t = time.time() - self.t0
        return 14.0 + 2.0*math.sin(t / 10.0)
