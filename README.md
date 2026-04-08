# 🌩️ W-BOSS (Weather Battle Operations Support System)

![Version](https://img.shields.io/badge/version-2.2-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)

**W-BOSS (기상 기반 작전 지원 시스템)**은 대한민국 공군의 작전 및 훈련 통제를 지원하기 위해 개발된 종합 기상 대시보드입니다. 기상청 API 및 자체 DB와 연동하여 실시간 기상 정보, 체감 온도, 기상 특보, 비정상 기후 감지 등의 데이터를 시각화하고, 국방부 온열지수 및 체감온도 지침에 따른 부대별 훈련 가용 여부를 직관적으로 제공합니다.

---

## 🌟 주요 기능

### 1. 종합 기상 대시보드 (Home)
- **실시간 기상 지도**: 전국 주요 관측소의 기온, 풍속, 강수량, 습도를 공간 데이터(SVG/SHP) 기반 맵으로 시각화합니다.
- **기상 특보 현황**: 현재 발효 중인 기상 특보를 단계별(주의보, 경보 등)로 분류하여 경고 패널에 표시합니다.
- **비정상 기후 감지**: 평년 통계(10년 평균) 대비 현재 기온 및 체감온도의 이상 징후를 감지하고 경고 배너를 출력합니다. (기온/체감온도 전환 가능)
- **타임라인 분석**: 과거 12시간부터 미래 12시간까지의 기상 변화 추이를 그래프로 제공합니다.

### 2. 시간대별 훈련 가능 현황 (`best_train_time.py`)
- 기상청 단기예보를 기반으로 부대별 시간대별 훈련 가능 여부를 분석합니다.
- 국방부 규정(여름철 온열지수, 겨울철 체감온도)에 따라 훈련 지수(초록/노랑/빨강)를 산출하여 테이블 및 차트로 제공합니다.

### 3. 체감온도 훈련 가능 분석 (`heatmap.py`)
- 기간별 체감온도 변화와 훈련 가능 여부를 히트맵(Heatmap) 형태로 시각화하여, 연간/월간 훈련 계획 수립을 지원합니다.

### 4. 상세 특보 현황 (`2_특보현황.py`)
- 기상청 발표 최신 특보 발효 현황, 예비 특보, 해제 특보를 상세하게 조회할 수 있습니다.

### 5. 인증 및 마이페이지 (`my_page.py`)
- **보안 인증**: 군번 기반 로그인, bcrypt 비밀번호 해싱, 로그인/접근 권한 제어.
- **마이페이지**: 사용자 프로필 조회, 계급 수정, 비밀번호 변경, 계정 탈퇴(일반 사용자).
- **감사 로그**: 본인의 접속 기록(IP, 체류 시간) 및 활동 감사 로그(AUDIT) 제공.
- **관리자(Admin) 기능**: 전체 사용자의 접속 로그 및 감사 로그 통합 열람.

---

## 📂 디렉토리 구조

프로젝트는 유지보수성과 확장성을 위해 기능별, UI별로 완전히 모듈화되어 있습니다.

```text
AirForceOne/
├── app_v2.py                  # 대시보드 메인 진입점 (st.navigation 라우팅)
├── DB_create.sql              # 데이터베이스 테이블 생성 스크립트
├── requirements.txt           # Python 패키지 의존성 목록
├── README.md                  # 프로젝트 안내 문서 (현재 파일)
├── CHANGELOG.md               # 버전별 업데이트 내역
│
├── functions/                 # 핵심 비즈니스 로직 및 컴포넌트 렌더링 함수
│   ├── auth_functions.py      # 로그인, 회원가입, 세션 관리
│   ├── audit_logger.py        # 접속 및 활동 감사 로그 기록
│   ├── dashboard_builder.py   # 메인 대시보드 레이아웃 조립
│   ├── anomaly_detector.py    # 비정상 기후 감지 알고리즘
│   ├── today_data.py          # DB 기반 당일 날씨/예보 데이터 조회
│   ├── sidebar_renderer.py    # 공통 사이드바 UI 렌더링
│   ├── css_loader.py          # 스타일시트 병합 및 주입
│   └── ...
│
├── pages/                     # Streamlit 네비게이션 서브 페이지
│   ├── 2_특보현황.py          # 상세 기상 특보 페이지
│   ├── best_train_time.py     # 시간대별 훈련 가용 분석 페이지
│   ├── heatmap.py             # 체감온도 히트맵 분석 페이지
│   ├── my_page.py             # 마이페이지 (프로필, 로그, 탈퇴)
│   ├── login_page.py          # 로그인 페이지
│   ├── register_page.py       # 회원가입 페이지
│   └── delete_page.py         # 회원탈퇴 처리 로직 (내부 라우팅용)
│
├── style/                     # 모듈화된 CSS 스타일시트
│   ├── base.css               # 기본 변수 및 리셋
│   ├── layout.css             # 그리드 레이아웃
│   ├── components.css         # 버튼, 카드 등 UI 요소
│   ├── topbar.css             # 상단 네비게이션 바
│   └── ...
│
└── utils/                     # 특정 도메인(훈련시간 분석 등) 전용 유틸리티
    ├── best_train_config.py
    ├── best_train_weather_api.py
    └── ...
```

---

## ⚙️ 설치 및 실행 방법

### 1. 환경 설정 및 의존성 설치
Python 3.11 이상 환경을 권장합니다.

```bash
# 레포지토리 클론 후 이동
cd AirForceOne

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 설정
MySQL 또는 MariaDB 환경이 필요합니다.
1. 데이터베이스 생성 및 접속
2. `DB_create.sql` 스크립트를 실행하여 테이블 구조(USERS, ACCESS_LOG, AUDIT_LOG, 기상 데이터 테이블 등)를 생성합니다.
3. 프로젝트 루트에 `.env` 파일을 생성하고 DB 접속 정보 및 기상청 API 키를 설정합니다.

```env
# .env 예시
DB_HOST=localhost
DB_USER=root
DB_PASS=your_password
DB_NAME=weather_db
SHORT_TERM_FORECAST_API_KEY=your_api_key_here
```

### 3. 애플리케이션 실행
메인 진입점인 `app_v2.py`를 Streamlit으로 실행합니다.

```bash
streamlit run app_v2.py
```
브라우저에서 `http://localhost:8501`로 접속하여 확인할 수 있습니다.

---

## 🔒 계정 및 권한 안내

가입 시 입력하는 **군번 형식**에 따라 자동으로 권한(Role)이 부여됩니다.

| 구분 | 군번 형식 | 예시 | 부여 권한 |
|---|---|---|---|
| **장교** | `YY-NNNNN` (5자리) | `25-12345` | `officer` |
| **부사관** | `YY-NNNNNN` (6자리) | `22-123456` | `nco` |
| **병** | `YY-NNNNNNNN` (8자리)| `26-12345678` | `soldier` |
| **관리자** | (DB 수동 설정) | `admin` | `admin` (전체 로그 열람 가능) |

> **참고**: 학습 및 테스트 목적으로 생성된 임시 계정의 비밀번호는 `acorn1234`로 통일되어 있습니다. 실제 운영 시에는 반드시 강력한 비밀번호 정책을 적용해야 합니다.

---

## 🚀 최근 주요 업데이트 (v2.2)

- **마이페이지 도입**: 프로필 조회, 계급 수정, 비밀번호 변경 기능 추가.
- **감사 로그 시스템**: 로그인/로그아웃, 정보 수정, 페이지 접근 등 모든 주요 활동에 대한 Audit Log 기록 (`AUDIT_LOG` 테이블).
- **계정 탈퇴 기능**: 마이페이지 내에서 비밀번호 재확인 후 안전한 계정 탈퇴(Soft Delete) 지원.
- **비정상 감지 고도화**: 체감온도뿐만 아니라 '기온' 기준의 비정상 감지 모드 추가 및 UI 토글 기능 적용.
- **라우팅 안정화**: `st.navigation` 기반 라우팅에서 발생하던 페이지 이동 오류(`StreamlitPageNotFoundError`) 완전 해결.

---
*Developed for Air Force 1 · 7기 공통프로젝트 · 2026.03*
