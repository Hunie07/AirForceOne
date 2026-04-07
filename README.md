# 🌤️ W-BOSS (Weather Base Operations Support System)

> 기상 데이터를 기반으로 군 작전 및 훈련 의사결정을 지원하는 통합 대시보드

---

## 📌 프로젝트 개요

**W-BOSS**는 실시간 기상 데이터와 과거 기후 데이터를 결합하여  
훈련 가능 여부를 빠르게 판단할 수 있도록 설계된 **의사결정 지원 시스템**입니다.

단순 시각화가 아닌,  
👉 **“지금 훈련 가능한가?”를 바로 판단할 수 있는 시스템**에 초점을 맞췄습니다.

---

## 🎯 개발 목표

- 실시간 기상 데이터를 활용한 **판단 보조 UI**
- 복잡한 데이터를 **직관적인 시각화로 단순화**
- 인증/로그 시스템을 포함한 **운영 가능한 구조**

---

## 🧩 핵심 기능

### 🛡️ 실시간 현황 대시보드
- 단기예보 API 기반 시간대별 훈련 가능 여부 분석
- 체감온도 / 풍속 / 강수 기반 위험도 판단
- 사용자 기준 작전 환경 제공

---

### 🌡️ 연간 훈련가용 판정 현황
- 2020 ~ 2025 데이터 기반 분석
- 히트맵 기반 패턴 시각화
- 월별 / 일별 훈련 가능 날짜 분석

---

### 🏠 메인 대시보드
- 핵심 기능 빠른 접근
- 요약 카드 기반 정보 전달
- 전체 흐름을 연결하는 허브 역할

---

### 🔐 인증 및 로그 시스템
- 군번 기반 로그인
- 회원가입 / 탈퇴 / 정보 수정
- 접속 로그 (access_log)
- 행위 로그 (audit_log)

---

## 🏗️ 프로젝트 구조

```
## 🏗️ 프로젝트 구조

```text
W_BOSS/
│
├── app.py                         # 메인 앱 (라우팅 및 진입점)
│
├── pages/
│   ├── best_train_time.py         # 실시간 현황 대시보드 페이지
│   ├── heatmap.py                 # 연간 훈련 가용 히트맵 페이지
│   ├── my_page.py                 # 마이페이지 (정보 수정 / 탈퇴)
│   ├── register_page.py           # 회원가입 페이지
│
├── ui/
│   ├── home.py                    # 메인 대시보드 UI
│   ├── sidebar.py                 # 사이드바 렌더링
│   ├── styles.py                  # 공통 스타일
│   ├── summary_cards.py           # 카드 UI 컴포넌트
│
├── services/
│   ├── auth_service.py            # 로그인 / 회원가입 로직
│   ├── session_service.py         # 세션 관리
│   ├── db_service.py              # DB 연결 및 쿼리
│
├── utils/
│   ├── best_train/                # 실시간 훈련 판단 모듈
│   │   ├── config.py              # API 키 / 지역 / 임계값 설정
│   │   ├── weather_api.py         # 단기예보 API 수집
│   │   ├── training_logic.py      # 훈련 가능 여부 판정 로직
│   │   └── forecast_pipeline.py   # 데이터 저장 파이프라인
│   │
│   ├── real_time/                 # 실시간 데이터 처리
│   │   ├── utils.py               # 공통 상수 / 유틸
│   │   ├── loaders.py             # 데이터 로딩 및 가공
│   │   └── charts.py              # 지도 / 차트 생성
│   │
│   ├── special_report/            # 기상 특보 처리
│   │   ├── api.py                 # 특보 API 호출
│   │   ├── preprocess.py          # 데이터 전처리
│   │   ├── storage.py             # DB 저장
│   │   └── query.py               # 조회 / 통계
│   │
│   └── heatmap/                   # 연간 분석 모듈
│       ├── config.py              # 설정값
│       ├── data.py                # 데이터 처리
│       ├── figures.py             # 그래프 생성
│       ├── ui_components.py       # UI 렌더링
│       └── bar_graph_function_sp.py # 등급 계산 로직
│
├── DB_create.sql                  # DB 스키마
└──requirements.txt              # 패키지 목록
```

---

## 🏗️ 시스템 아키텍처

Frontend (Streamlit)
    ↓
UI Layer
    ↓
Service Layer
    ↓
Database (MySQL / RDS)
    ↓
External API (기상청)

---

## 🧱 기술 스택

- Streamlit
- Python
- MySQL (AWS RDS)
- Pandas
- Altair / Folium / Plotly

---

## 📊 데이터 기준

- 2020 ~ 2025
- 5개 지역

---

## ⚙️ 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🪖 프로젝트 정보

- 2026.03 ~ 2026.04
- 공군 프로젝트

---

## 🎯 한 줄 요약

기상 데이터를 판단 가능한 정보로 변환하는 시스템
