import numpy as np, wave, math
class MicSource:
    def __init__(self, path: str):
        self.wf = wave.open(path, "rb")
        self.rate = self.wf.getframerate()
        self.nch = self.wf.getnchannels()
        self.chunk = int(self.rate * 1.0)  # 1s
    def read_brpm(self) -> float:
        data = self.wf.readframes(self.chunk)
        if len(data)==0: self.wf.rewind(); data = self.wf.readframes(self.chunk)
        x = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        if self.nch==2: x = x[::2]
        x = x / (np.max(np.abs(x))+1e-6)
        ac = np.correlate(x, x, mode="full")[len(x)-1:]
        low, high = int(self.rate/6.0), int(self.rate/0.3)
        seg = ac[low:high]; peak = int(np.argmax(seg))+low
        period = max(peak,1); brpm = 60.0 / (period/self.rate)
        return float(np.clip(brpm, 6, 40))
