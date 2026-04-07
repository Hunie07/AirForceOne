"""
기상청 특보 API 수집 모듈 (기상청 API허브)
- 특보 구역: wrn_reg.php
- 특보 자료: wrn_met_data.php
"""

import requests
import pandas as pd
from datetime import datetime, timedelta

API_BASE  = "https://apihub.kma.go.kr/api/typ01/url"
ZONES_URL = f"{API_BASE}/wrn_reg.php"
DATA_URL  = f"{API_BASE}/wrn_met_data.php"

# WRN 코드 → 특보 종류
WRN_CODE_MAP = {
    "W": "강풍",  "S": "대설",  "R": "호우",  "C": "한파",
    "Y": "황사",  "D": "건조",  "T": "태풍",  "H": "폭풍해일",
    "V": "풍랑",  "E": "폭염",
}

# LVL 코드 → 특보 수준
LVL_MAP = {"1": "예비", "2": "주의보", "3": "경보"}

# CMD 코드 → 특보 명령
CMD_MAP = {
    "1": "발표", "2": "대치", "3": "해제",
    "4": "대치해제", "5": "연장", "6": "변경", "7": "변경해제",
}

# 발효중으로 간주하는 CMD 코드 (해제 계열 제외)
ACTIVE_CMDS = {"1", "2", "5", "6"}

# 특보 종류 목록 (영향 테이블 열 순서)
REPORT_TYPES = ["강풍", "풍랑", "대설", "호우", "한파", "황사", "건조", "폭풍해일"]

# 관심 5개 군 (행 순서 고정)
REGIONS = ["연천군", "철원군", "양구군", "화천군", "고성군"]

# 5개 군별 상위 행정구역 키워드 매핑
# 경기도·강원도·전국 단위 특보도 해당 군에 영향을 미치므로 함께 수집합니다.
REGION_PARENT_MAP: dict[str, list[str]] = {
    "연천군": ["경기"],
    "철원군": ["강원"],
    "양구군": ["강원"],
    "화천군": ["강원"],
    "고성군": ["강원"],
}

# KMA 구역코드 → 지역명 하드코딩 (wrn_reg.php 타임아웃 시 fallback)
_ZONE_FALLBACK: dict[str, str] = {
    # 경기도
    "L1011100": "경기남부",         "L1011200": "연천군",
    "L1011300": "경기북부",         "L1011400": "경기동부",
    # 강원도
    "L1021100": "강원중부",         "L1021200": "강원남부",
    "L1021300": "철원군",           "L1021400": "화천군",
    "L1021500": "강원북부",         "L1021600": "강원중북부",
    "L1021700": "강원북부내륙",     "L1021710": "양구군내륙",
    "L1021800": "강원남부내륙",
    # 강원 동해안
    "L1020100": "강원북부동해안",   "L1020200": "강원중부동해안",
    "L1020300": "강원남부동해안",   "L1020610": "고성군동해안",
    # 서울·인천·경기
    "L1100100": "서울",             "L1200100": "인천",
    "L1300100": "경기",
    # 충청
    "L1400100": "충북북부",         "L1400200": "충북남부",
    "L1500100": "충남북부",         "L1500200": "충남남부",
    "L1600100": "대전",
    # 경상
    "L1700100": "경북북부",         "L1700200": "경북남부",
    "L1800100": "경남서부",         "L1800200": "경남동부",
    "L1900100": "대구",             "L2000100": "부산",
    "L2100100": "울산",
    # 전라·제주
    "L2200100": "전북북부",         "L2200200": "전북남부",
    "L2300100": "전남북부",         "L2300200": "전남남부",
    "L2400100": "광주",             "L2500100": "제주",
    "L2500200": "제주산지",
    # 앞바다·먼바다 (주요)
    "W1100100": "서해중부앞바다",   "W1100200": "서해남부앞바다",
    "W1200100": "동해중부앞바다",   "W1200200": "동해남부앞바다",
    "W1300100": "남해서부앞바다",   "W1300200": "남해동부앞바다",
    "W1400100": "제주도근해",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def get_auth_key() -> str:
    """secrets.toml [api] 섹션에서 API 인증키를 반환합니다."""
    import streamlit as st
    key = st.secrets['api']['REPORT_DATA_API_SERVICE_KEY']
    if not key:
        raise ValueError("REPORT_DATA_API_SERVICE_KEY not set in .toml")
    return key

def fetch_alert_zones(auth_key: str) -> pd.DataFrame:
    """특보 구역 목록을 수집합니다. (wrn_reg.php)
    API 실패 시 _ZONE_FALLBACK 하드코딩 데이터로 대체합니다.
    컬럼: REG_ID, REG_NAME
    """
    try:
        resp = requests.get(
            ZONES_URL,
            params={"tmfc": "0", "authKey": auth_key},
            headers=HEADERS, timeout=(5, 30),
        )
        df = _parse_zone_text(resp.text)
        if not df.empty:
            return df
    except Exception:
        pass
    # fallback: 하드코딩 구역 데이터
    rows = [{"REG_ID": k, "REG_NAME": v} for k, v in _ZONE_FALLBACK.items()]
    return pd.DataFrame(rows)


def fetch_alert_data(
    auth_key: str,
    tmfc1: str = None,
    tmfc2: str = None,
    wrn: str = "A",
    reg: str = "0",
) -> pd.DataFrame:
    """특보 자료를 수집합니다. (wrn_met_data.php)
    컬럼: TM_FC, TM_EF, TM_IN, STN, REG_ID, WRN, LVL, CMD, GRD, CNT
    tmfc1/tmfc2 미입력 시 7일 전부터 현재까지 조회 (발효 중인 특보 누락 방지)
    """
    now   = datetime.now()
    tmfc1 = tmfc1 or (now - timedelta(days=7)).strftime("%Y%m%d") + "0000"
    tmfc2 = tmfc2 or now.strftime("%Y%m%d%H%M")
    resp  = requests.get(
        DATA_URL,
        params={
            "reg": reg, "wrn": wrn,
            "tmfc1": tmfc1, "tmfc2": tmfc2,
            "disp": "0", "help": "0",
            "authKey": auth_key,
        },
        headers=HEADERS, timeout=(5, 60),
    )
    return _parse_alert_text(resp.text)


# ── 내부 파싱 함수 ───────────────────────────────────────────

def _parse_zone_text(text: str) -> pd.DataFrame:
    """wrn_reg.php 공백 구분 텍스트 → DataFrame"""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 7:
            continue
        rows.append({
            "REG_ID":   parts[0],
            "TM_ST":    parts[1],
            "TM_ED":    parts[2],
            "REG_SP":   parts[3],
            "REG_UP":   parts[4],
            "REG_KO":   parts[5],
            "REG_NAME": parts[-1],
        })
    return pd.DataFrame(rows)


def _parse_alert_text(text: str) -> pd.DataFrame:
    """wrn_met_data.php 쉼표 구분 텍스트 → DataFrame"""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 10:
            continue
        rows.append({
            "TM_FC":  parts[0],
            "TM_EF":  parts[1],
            "TM_IN":  parts[2],
            "STN":    parts[3],
            "REG_ID": parts[4],
            "WRN":    parts[5],
            "LVL":    parts[6],
            "CMD":    parts[7],
            "GRD":    parts[8],
            "CNT":    parts[9],
        })
    return pd.DataFrame(rows)
