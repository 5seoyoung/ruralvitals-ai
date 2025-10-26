# edge_agent/signals/ppg.py
import csv

class PPGSource:
    def __init__(self, csv_path: str):
        self.rows = []
        with open(csv_path, newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                self.rows.append(row)
        self.i = 0

    def read_hr(self) -> float:
        if not self.rows:
            return 72.0
        if self.i >= len(self.rows):
            self.i = 0
        try:
            return float(self.rows[self.i].get("hr_bpm", 72.0))
        finally:
            self.i += 1
