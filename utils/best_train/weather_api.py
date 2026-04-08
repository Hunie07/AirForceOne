"""
기상청 단기예보 API 호출 및 DataFrame 반환.
캐싱은 Streamlit @st.cache_data 로 처리.
"""
import time

import numpy as np
import pandas as pd
import requests
import streamlit as st
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta, timezone

from utils.best_train.config import (
    SERVICE_KEY,
    AREA_INFO,
    API_URL,
    API_ROWS,
    API_CACHE_TTL,
)
from utils.best_train.training_logic import compute_apparent_temperatures


_REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/119.0.0.0 Safari/537.36'
    )
}

_CATEGORY_MAP = {
    'TMP': '기온',
    'WSD': '풍속',
    'REH': '습도',
    'PCP': '강수량',
}


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────

def _build_params(base_date: str, base_time: str, nx: int, ny: int) -> dict:
    return {
        'serviceKey': SERVICE_KEY,
        'pageNo':     '1',
        'numOfRows':  str(API_ROWS),
        'dataType':   'XML',
        'base_date':  base_date,
        'base_time':  base_time,
        'nx':         nx,
        'ny':         ny,
    }


def _fetch_area(
    name: str,
    info: dict,
    base_date: str,
    base_time: str,
    target_dates: list[str],
) -> tuple[list[dict], str | None]:
    """
    단일 지역 API 호출 → 파싱된 row 리스트 반환.
    오류가 있으면 ([], 오류메시지) 반환.
    """
    params = _build_params(base_date, base_time, info['nx'], info['ny'])
    try:
        time.sleep(np.random.uniform(0.1, 0.5))
        res = requests.get(API_URL, params=params, headers=_REQUEST_HEADERS, timeout=15)
        res.raise_for_status()
        root = ET.fromstring(res.content)

        result_code = root.find('.//resultCode')
        if result_code is not None and (result_code.text or '').strip() != '00':
            msg = root.find('.//resultMsg')
            return [], f"{name}: {(msg.text or 'API 오류').strip() if msg is not None else 'API 오류'}"

        items = root.findall('.//item')
        if not items:
            return [], f"{name}: 데이터 없음"

        # ── 시간별 데이터 누적 ─────────────────────────────────────────
        temp_dict: dict[tuple, dict] = {}
        for item in items:
            f_date = (item.findtext('fcstDate') or '').strip()
            if f_date not in target_dates:
                continue
            f_time = (item.findtext('fcstTime') or '').strip()[:2]
            cat    = (item.findtext('category') or '').strip()
            val_text = (item.findtext('fcstValue') or '').strip()
            if not val_text:
                continue

            col_name = _CATEGORY_MAP.get(cat)
            if col_name is None:
                continue

            date_key = f"{int(f_date[4:6])}/{int(f_date[6:8])}"
            key = (date_key, f_time)
            temp_dict.setdefault(key, {})
            try:
                temp_dict[key][col_name] = float(val_text)
            except ValueError:
                pass

        rows = []
        for (date, hour), v in temp_dict.items():
            if '기온' not in v:
                continue
            rows.append({
                '지역':  name,
                '날짜':  date,
                '시간':  hour,
                '기온':  v.get('기온',   0.0),
                '풍속':  v.get('풍속',   0.0),
                '습도':  v.get('습도',   0.0),
                '강수량': v.get('강수량', 0.0),
            })
        return rows, None

    except Exception as e:
        return [], f"{name}: {e}"


# ── 공개 API ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=API_CACHE_TTL, show_spinner=False)
def get_weather_data() -> pd.DataFrame:
    """
    오늘~모레 3일치 기상 데이터를 수집해 반환.

    DataFrame attrs
    ---------------
    base_date : str   예보 기준 날짜(YYYYMMDD)
    base_time : str   예보 기준 시각(HHMM)

    오류 발생 시 st.session_state['api_errors'] 에 목록 저장.
    데이터가 전혀 없으면 빈 DataFrame 반환.
    """
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    yesterday  = now - timedelta(days=1)
    base_date  = yesterday.strftime('%Y%m%d')
    base_time  = "2300"
    target_dates = [(now + timedelta(days=i)).strftime('%Y%m%d') for i in range(3)]

    all_rows: list[dict] = []
    errors:   list[str]  = []

    for name, info in AREA_INFO.items():
        rows, err = _fetch_area(name, info, base_date, base_time, target_dates)
        all_rows.extend(rows)
        if err:
            errors.append(err)

    if errors:
        st.session_state['api_errors'] = errors

    _empty = pd.DataFrame(columns=['지역', '날짜', '시간', '기온', '풍속', '습도', '강수량'])
    _empty.attrs['base_date'] = base_date
    _empty.attrs['base_time'] = base_time

    if not all_rows:
        return _empty

    df = pd.DataFrame(all_rows)
    df = compute_apparent_temperatures(df)
    df.attrs['base_date'] = base_date
    df.attrs['base_time'] = base_time
    return df
