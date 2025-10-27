# app/pages/2_ℹ️_About.py
import streamlit as st

st.set_page_config(page_title="About RuralVitals", page_icon="ℹ️", layout="wide")
st.title("ℹ️ About — RuralVitals Edge AI")

st.markdown("""
**RuralVitals**는 카메라·오디오·PPG 신호를 **엣지 디바이스**(Jetson/RPi)에서
로컬 추론하여 이상 징후(무동작, 호흡/심박 이탈)를 감지하고, **네트워크 없이도 경보/로깅** 가능한
농촌형 디지털 돌봄 모델입니다.

### 왜 엣지인가?
- 통신 불안정 지역에서도 동작(Offline-first)
- 프라이버시 보호(로우데이터 저장 X, 이벤트/특징만 저장)
- 저비용 다인 커버리지(가구/시설 단위 배치 용이)

### 데모 구성
1) `edge_agent/main.py` : Edge 추론 루프 → SQLite 로깅  
2) `app/app.py` : 대시보드(UI) → 다인 KPI/카드/피드/임계치  
3) `edge_agent/configs/default.yaml` : 임계치/알림/대상자 설정

### 확장
- Notifier BLE/SMS 연동
- Jetson TensorRT로 모델 교체(ONNX→TRT)
- LoRa/게이트웨이 연동 및 군 단위 통합관제
""")
