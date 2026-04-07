"""
W-BOSS 공통 기상 판정 유틸리티
────────────────────────────────
- 훈련 판정 상태 색상·이모지 상수
- 특보 기반 판정 오버라이드
- 작전 시간대 정의
- 지역 좌표 / 지도 색상
"""
from utils.best_train.training_logic import get_continuous_ranges

# ── 표시 상수 ─────────────────────────────────────────────────────────────────
STATUS_EMOJI: dict[str, str] = {
    "가능": "🟢", "주의": "🟡", "제한": "🟠", "중지": "🔴",
}

METRIC_UNIT: dict[str, str] = {
    "기온": "℃", "풍속": "m/s", "습도": "%",
    "강수량": "mm", "체감온도": "℃", "온도지수": "℃",
}

DAY_LABELS: list[str] = ["오늘", "내일", "모레"]

# ── 작전 시간대: D일 06시~23시 + D+1일 00시~05시 ─────────────────────────────
DUTY_CUR:  list[str] = [f"{i:02d}" for i in range(6, 24)]   # 06~23시 (당일)
DUTY_NEXT: list[str] = [f"{i:02d}" for i in range(0, 6)]    # 00~05시 (익일)

# ── 지도 마커 색상 ────────────────────────────────────────────────────────────
MAP_COLOR: dict[str, str] = {
    "가능": "#00c853", "주의": "#ffd600", "제한": "#ff6d00", "중지": "#d50000",
}

# ── 지역 좌표 (군청 기준, WGS84) ─────────────────────────────────────────────
REGION_COORDS: dict[str, tuple[float, float]] = {
    "연천": (38.096494, 127.075078),
    "철원": (38.146789, 127.312481),
    "양구": (38.110193, 127.990088),
    "화천": (38.106470, 127.708163),
    "고성": (38.380762, 128.468111),
}

# ── 훈련 판정에 반영할 특보 종류 ─────────────────────────────────────────────
ALERT_TRAINING_TYPES: set[str] = {
    "폭염", "한파", "호우", "태풍", "대설", "강풍", "황사", "건조",
}

# ── 해양 구역 제외 키워드 ─────────────────────────────────────────────────────
MARITIME_KEYWORDS: list[str] = [
    "동해안", "서해", "남해", "앞바다", "먼바다", "근해", "해상",
]

# ── 상태 심각도 우선순위 ──────────────────────────────────────────────────────
_STATUS_PRI:      dict[str, int] = {"가능": 0, "주의": 1, "제한": 2, "중지": 3}
_STATUS_FROM_PRI: dict[int, str] = {0: "가능", 1: "주의", 2: "제한", 3: "중지"}


# ── 판정 함수 ─────────────────────────────────────────────────────────────────
def apply_alert_to_status(base_status: str, alert_level: str | None) -> str:
    """온도 기준 등급에 특보 수준을 오버라이드하여 최종 등급 반환.

    - 경보   → 무조건 중지
    - 주의보 → 최소 제한 (온도 기준이 이미 더 심각하면 그대로)
    """
    if alert_level == "경보":
        return "중지"
    if alert_level == "주의보":
        return _STATUS_FROM_PRI[max(_STATUS_PRI.get(base_status, 0), 2)]
    return base_status

def restricted_range_str(today_vals: list) -> str:
    """훈련 제한(주의·제한·중지) 연속 구간 문자열. 없으면 빈 문자열."""
    ranges = get_continuous_ranges(today_vals, ["주의", "제한", "중지"])
    if not ranges:
        return ""
    return ",  ".join(
        f"{s:02d}:00 ~ {e + 1:02d}:00"
        for s, e in sorted(ranges, key=lambda x: x[0])
    )
