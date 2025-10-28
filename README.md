## RuralVitals — 충북 농촌형 엣지 돌봄 (Rural Edge AI Monitoring System)

> **비착용·오프라인·다인 커버리지 기반의 실시간 생체신호 모니터링 시스템**
> Jetson 엣지 디바이스에서 **카메라·PPG·마이크 신호를 로컬 추론**하고,
> 네트워크 연결이 불안정한 농촌 환경에서도 즉시 위험을 감지해 **복지사·가족에게 BLE/문자 알림**을 전송합니다.

---

### Live Demo

> ▶ **[서비스 데모 바로가기](https://5seoyoung.github.io/ruralvitals-ai/)**
> (GitHub Pages + Streamlit Cloud Embed)
>
> 실시간 대시보드에서
>
> * 충청북도 **시·군 단위 필터링**,
> * 대상자별 **심박/호흡 이상 탐지**,
> * 이벤트 타임라인 및 **임계치 설정** 기능을 확인할 수 있습니다.

---

### System Overview

| 구성요소                                | 설명                                               |
| ----------------------------------- | ------------------------------------------------ |
| **Edge Device (Jetson Nano / RPi)** | 카메라·마이크·PPG 센서로 생체신호 수집 및 로컬 추론 수행               |
| **Edge AI Model**                   | CNN+LSTM 기반 생체 이상탐지 (호흡·심박·움직임) + 규칙기반 임계값 하이브리드 |
| **Local Storage**                   | SQLite 기반 이벤트 로깅 및 오프라인 버퍼링 (통신 복구 시 자동 재전송)     |
| **Dashboard (Streamlit)**           | 시군구 필터, 대상자 카드, 이벤트 로그, 타임라인, 임계치 설정 UI 제공       |
| **BLE / SMS 알림**                    | Edge 단말에서 직접 복지사·가족에게 경보 전송 (로컬 네트워크 의존 최소화)     |

---

### Model Architecture

```
[Camera / PPG / Mic Input]
        │
        ▼
 ┌────────────┐
 │ Preprocessor │ (조도 보정, 노이즈 제거, 정규화)
 └────────────┘
        │
        ▼
 ┌────────────────────┐
 │ CNN + LSTM Hybrid │ (단기 패턴 + 장기 리듬)
 └────────────────────┘
        │
        ▼
[Abnormality Score → Rule-based Thresholding]
        │
        ▼
[Local Event Trigger + BLE/SMS Notification]
```

---

### Dashboard Features

| 기능              | 설명                                                     |
| --------------- | ------------------------------------------------------ |
| **시·군 필터링** | 충북 전체/개별 지역 단위로 대상자 상태 확인                              |
| **대상자 카드**   | 실시간 심박·호흡률·최근 활동 및 위험 상태 시각화                           |
| **이벤트 로그**   | Edge에서 감지된 ALERT/INFO 이력 자동 업데이트                       |
| **이벤트 타임라인** | 최근 24시간 내 발생한 이벤트를 유형별로 시각화                            |
| **임계치 설정**   | Edge 추론 모델의 경고 기준값 동적 조정 (inactivity_sec, brpm_high 등) |
| **오프라인 버퍼링** | 통신 끊김 시에도 로컬 DB에 임시 저장 후 자동 재전송                        |

---

### Local Edge Demo

```bash
# 1️환경 설정
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-edge.txt

# 2️샘플 이벤트 시드 데이터 생성
python scripts/seed_demo.py

# 3️로컬 엣지 에이전트 실행
python -m edge_agent.main

# 4️Streamlit 대시보드 실행
streamlit run app/app.py
```

> Edge Agent는 `edge_agent/rva_events.db` 에 이벤트를 로깅하고
> Streamlit 대시보드는 이를 실시간으로 시각화합니다.

---

###  Repository Structure

```
ruralvitals-ai/
├── app/                    # Streamlit UI
│   ├── app.py
│   └── components/
├── edge_agent/             # Edge inference + event logging
│   ├── main.py
│   ├── utils/
│   ├── models/
│   └── examples/
├── scripts/
│   ├── seed_demo.py        # DB 샘플 시드 스크립트
│   └── eval_test.py
├── data/
│   └── resident_registry.csv
├── requirements-edge.txt
└── README.md
```

---

### Deployment

| 구성                       | 기술스택                                        |
| ------------------------ | ------------------------------------------- |
| **Frontend / Dashboard** | Streamlit Cloud                             |
| **Public Demo Hosting**  | GitHub Pages (iframe embed)                 |
| **Edge Runtime**         | Python 3.11 / OpenCV / ONNX Runtime / Bleak |
| **Data Storage**         | SQLite (local)                              |
| **Alert Interface**      | BLE / SMS Gateway (Twilio optional)         |

---

###  Use Case: 충북 지역 돌봄 센터

* Jetson Nano 기반 엣지 모듈을 **농촌 독거노인 가정** 또는 **소규모 요양시설**에 설치
* 네트워크 불안정 구간에서도 **Edge 추론 + 오프라인 저장 → BLE 알림**으로 대응
* 복지사 단말에서는 Streamlit 대시보드로 각 대상자의 실시간 상태 모니터링

---

###  Roadmap

| 단계            | 목표                  | 주요 내용                         |
| ------------- | ------------------- | ----------------------------- |
| **1단계 (완료)**  | Edge AI 추론 파이프라인 구축 | Jetson 실시간 추론 + Streamlit 시각화 |
| **2단계 (진행중)** | 지역별 실증형 테스트         | 충북 복지기관/보건소 협업 시뮬레이션          |
| **3단계 (예정)**  | 양산형 MVP 개발          | 센서 모듈 최적화 + OTA 자동 업데이트       |
| **4단계 (확장)**  | 지자체 도입 및 정책 연계      | 지역돌봄 실증사업·디지털포용사업과 연계 추진      |

---

###  Awards & References
* **2025 지역주도 디지털혁신 지원사업 ICT 융합 공모전** 출품작
---

### 🔗 Links

* **Live Demo:** [https://5seoyoung.github.io/ruralvitals-ai/](https://5seoyoung.github.io/ruralvitals-ai/)
* **Streamlit Cloud:** [https://ruralvitals-ai.streamlit.app](https://ruralvitals-ai.streamlit.app)
* **GitHub Repo:** [https://github.com/5seoyoung/ruralvitals-ai](https://github.com/5seoyoung/ruralvitals-ai)

---
