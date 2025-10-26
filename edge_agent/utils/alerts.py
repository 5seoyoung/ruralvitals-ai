# edge_agent/utils/alerts.py
from datetime import datetime

class Notifier:
    def __init__(self, mode: str = "none", **kwargs):
        self.mode = mode
        self.kwargs = kwargs

    def send(self, title: str, message: str) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.mode == "none":
            print(f"[ALERT][{now}] {title}: {message}")
            return True
        if self.mode == "ble":
            # TODO: bleak로 BLE notify 구현
            print(f"[BLE][{now}] {title}: {message}")
            return True
        if self.mode == "sms":
            # TODO: SMS 게이트웨이 연동
            print(f"[SMS][{now}] {title}: {message}")
            return True
        return False
