import streamlit as st

# ── API 키 ──────────────────────────────────────
SERVICE_KEY = st.secrets["api"]["SHORT_TERM_FORECAST_API_KEY"]

# ── 지역 좌표 ────────────────────────────────────
AREA_INFO: dict[str, dict] = {
    '연천': {'nx': 61, 'ny': 138},
    '철원': {'nx': 65, 'ny': 139},
    '양구': {'nx': 77, 'ny': 139},
    '화천': {'nx': 72, 'ny': 139},
    '고성': {'nx': 85, 'ny': 145},
}

# ── 계절 구분 ────────────────────────────────────
SUMMER_MONTHS: list[int] = [5, 6, 7, 8, 9]

# ── 시간 범위 ────────────────────────────────────
ALL_HOURS: list[str]  = [f"{i:02d}" for i in range(24)]
DAY_HOURS: list[str]  = [f"{i:02d}" for i in range(6, 18)]   # 주간 훈련 대상 시간

# ── 판정 색상 ────────────────────────────────────
STATUS_COLOR: dict[str, str] = {
    'go':       '#00c853',
    'caution':  '#ffd600',
    'restrict': '#ff6d00',
    'stop':     '#d50000',
}

# ── 기상청 API ───────────────────────────────────
API_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
API_ROWS = 1000
API_CACHE_TTL = 3600   # seconds

# ── 훈련 판정 임계값 ──────────────────────────────
# 여름(온도지수 기준) #국방부 지침 상 / 부분제한 또는 제한을 제한으로 통합하였음
SUMMER_THRESHOLDS = [
    (32.0, '중지', 'stop'),
    (29.5, '제한', 'restrict'),
    (26.5, '주의', 'caution'),
]
# 겨울(체감온도 기준)
WINTER_THRESHOLDS = [
    (-24.0, '중지', 'stop'),
    (-18.0, '제한', 'restrict'),
    (-10.0, '주의', 'caution'),
]
