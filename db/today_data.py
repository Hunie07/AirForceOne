"""
functions/today_data.py
W-BOSS  오늘 날씨 데이터 조회 모듈
──────────────────────────────────────
• DB 쿼리 전용 (직접 API 호출 없음)
• forecast_data 테이블 : 오늘 예보 데이터 (지역별)
• asos_history 테이블  : 오늘 실측 관측 데이터 (관측소별)
• operation_available_day 테이블 : 오늘 훈련 가능 여부 (지역별)

사용 예시:
    from today_data import (
        get_today_forecast,
        get_today_asos,
        get_today_availability,
        get_today_summary,
    )
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

# db_connection 임포트 — 패키지 경로 및 직접 경로 모두 지원
try:
    from db_connection import get_cursor
except ImportError:
    from db_connection import get_cursor


# ════════════════════════════════════════════════════════════════════
# forecast_data 조회
# ════════════════════════════════════════════════════════════════════

def get_today_forecast(region_id: Optional[int] = None) -> list[dict]:
    """
    오늘 날짜의 예보 데이터를 조회한다.

    Parameters
    ----------
    region_id : int | None
        특정 지역 ID. None이면 전체 지역 조회.

    Returns
    -------
    list[dict]
        forecast_data 레코드 목록.
        각 dict: id, region_id, forecast_base_time, forecast_target_time,
                 tmp, wsd, reh, precipitation, apparent_temp, heat_index,
                 is_available, collected_at
    """
    today = date.today().isoformat()  # 'YYYY-MM-DD'
    try:
        with get_cursor() as (cur, _):
            if region_id is not None:
                cur.execute(
                    """
                    SELECT fd.id, fd.region_id, r.region_name,
                           fd.forecast_base_time, fd.forecast_target_time,
                           fd.tmp, fd.wsd, fd.reh, fd.precipitation,
                           fd.apparent_temp, fd.heat_index,
                           fd.is_available, fd.collected_at
                    FROM   forecast_data fd
                    JOIN   region r ON r.region_id = fd.region_id
                    WHERE  DATE(fd.forecast_target_time) = %s
                      AND  fd.region_id = %s
                    ORDER  BY fd.forecast_target_time ASC
                    """,
                    (today, region_id),
                )
            else:
                cur.execute(
                    """
                    SELECT fd.id, fd.region_id, r.region_name,
                           fd.forecast_base_time, fd.forecast_target_time,
                           fd.tmp, fd.wsd, fd.reh, fd.precipitation,
                           fd.apparent_temp, fd.heat_index,
                           fd.is_available, fd.collected_at
                    FROM   forecast_data fd
                    JOIN   region r ON r.region_id = fd.region_id
                    WHERE  DATE(fd.forecast_target_time) = %s
                    ORDER  BY fd.region_id ASC, fd.forecast_target_time ASC
                    """,
                    (today,),
                )
            return cur.fetchall() or []
    except Exception as exc:
        logger.error(f"[today_data] get_today_forecast 오류: {exc}")
        return []


def get_today_forecast_latest(region_id: Optional[int] = None) -> list[dict]:
    """
    오늘 날짜의 최신 예보 발표 기준 데이터만 조회한다.
    (가장 최근 forecast_base_time 기준)

    Parameters
    ----------
    region_id : int | None
        특정 지역 ID. None이면 전체 지역 조회.

    Returns
    -------
    list[dict]
        최신 발표 기준 예보 레코드 목록.
    """
    today = date.today().isoformat()
    try:
        with get_cursor() as (cur, _):
            if region_id is not None:
                cur.execute(
                    """
                    SELECT fd.id, fd.region_id, r.region_name,
                           fd.forecast_base_time, fd.forecast_target_time,
                           fd.tmp, fd.wsd, fd.reh, fd.precipitation,
                           fd.apparent_temp, fd.heat_index,
                           fd.is_available, fd.collected_at
                    FROM   forecast_data fd
                    JOIN   region r ON r.region_id = fd.region_id
                    WHERE  DATE(fd.forecast_target_time) = %s
                      AND  fd.region_id = %s
                      AND  fd.forecast_base_time = (
                               SELECT MAX(fd2.forecast_base_time)
                               FROM   forecast_data fd2
                               WHERE  fd2.region_id = fd.region_id
                                 AND  DATE(fd2.forecast_target_time) = %s
                           )
                    ORDER  BY fd.forecast_target_time ASC
                    """,
                    (today, region_id, today),
                )
            else:
                cur.execute(
                    """
                    SELECT fd.id, fd.region_id, r.region_name,
                           fd.forecast_base_time, fd.forecast_target_time,
                           fd.tmp, fd.wsd, fd.reh, fd.precipitation,
                           fd.apparent_temp, fd.heat_index,
                           fd.is_available, fd.collected_at
                    FROM   forecast_data fd
                    JOIN   region r ON r.region_id = fd.region_id
                    WHERE  DATE(fd.forecast_target_time) = %s
                      AND  fd.forecast_base_time = (
                               SELECT MAX(fd2.forecast_base_time)
                               FROM   forecast_data fd2
                               WHERE  fd2.region_id = fd.region_id
                                 AND  DATE(fd2.forecast_target_time) = %s
                           )
                    ORDER  BY fd.region_id ASC, fd.forecast_target_time ASC
                    """,
                    (today, today),
                )
            return cur.fetchall() or []
    except Exception as exc:
        logger.error(f"[today_data] get_today_forecast_latest 오류: {exc}")
        return []


# ════════════════════════════════════════════════════════════════════
# asos_history 조회
# ════════════════════════════════════════════════════════════════════

def get_today_asos(station_id: Optional[int] = None) -> list[dict]:
    """
    오늘 날짜의 ASOS 실측 관측 데이터를 조회한다.

    Parameters
    ----------
    station_id : int | None
        특정 관측소 ID. None이면 전체 관측소 조회.

    Returns
    -------
    list[dict]
        asos_history 레코드 목록.
        각 dict: id, station_id, station_name, region_id, region_name,
                 observed_at, temperature, humidity, precipitation,
                 wind_speed, wind_direction, apparent_temp, heat_index,
                 quality_flag, collected_at
    """
    today = date.today().isoformat()
    try:
        with get_cursor() as (cur, _):
            if station_id is not None:
                cur.execute(
                    """
                    SELECT ah.id, ah.station_id, s.station_name,
                           s.region_id, r.region_name,
                           ah.observed_at, ah.temperature, ah.humidity,
                           ah.precipitation, ah.wind_speed, ah.wind_direction,
                           ah.apparent_temp, ah.heat_index,
                           ah.quality_flag, ah.collected_at
                    FROM   asos_history ah
                    JOIN   asos_station s ON s.station_id = ah.station_id
                    JOIN   region r ON r.region_id = s.region_id
                    WHERE  DATE(ah.observed_at) = %s
                      AND  ah.station_id = %s
                    ORDER  BY ah.observed_at ASC
                    """,
                    (today, station_id),
                )
            else:
                cur.execute(
                    """
                    SELECT ah.id, ah.station_id, s.station_name,
                           s.region_id, r.region_name,
                           ah.observed_at, ah.temperature, ah.humidity,
                           ah.precipitation, ah.wind_speed, ah.wind_direction,
                           ah.apparent_temp, ah.heat_index,
                           ah.quality_flag, ah.collected_at
                    FROM   asos_history ah
                    JOIN   asos_station s ON s.station_id = ah.station_id
                    JOIN   region r ON r.region_id = s.region_id
                    WHERE  DATE(ah.observed_at) = %s
                    ORDER  BY ah.station_id ASC, ah.observed_at ASC
                    """,
                    (today,),
                )
            return cur.fetchall() or []
    except Exception as exc:
        logger.error(f"[today_data] get_today_asos 오류: {exc}")
        return []


def get_today_asos_latest(station_id: Optional[int] = None) -> list[dict]:
    """
    오늘 날짜의 각 관측소별 최신 관측값(가장 최근 observed_at)을 조회한다.

    Parameters
    ----------
    station_id : int | None
        특정 관측소 ID. None이면 전체 관측소 최신값 조회.

    Returns
    -------
    list[dict]
        각 관측소의 최신 관측 레코드.
    """
    today = date.today().isoformat()
    try:
        with get_cursor() as (cur, _):
            if station_id is not None:
                cur.execute(
                    """
                    SELECT ah.id, ah.station_id, s.station_name,
                           s.region_id, r.region_name,
                           ah.observed_at, ah.temperature, ah.humidity,
                           ah.precipitation, ah.wind_speed, ah.wind_direction,
                           ah.apparent_temp, ah.heat_index,
                           ah.quality_flag, ah.collected_at
                    FROM   asos_history ah
                    JOIN   asos_station s ON s.station_id = ah.station_id
                    JOIN   region r ON r.region_id = s.region_id
                    WHERE  DATE(ah.observed_at) = %s
                      AND  ah.station_id = %s
                      AND  ah.observed_at = (
                               SELECT MAX(ah2.observed_at)
                               FROM   asos_history ah2
                               WHERE  ah2.station_id = ah.station_id
                                 AND  DATE(ah2.observed_at) = %s
                           )
                    LIMIT  1
                    """,
                    (today, station_id, today),
                )
            else:
                cur.execute(
                    """
                    SELECT ah.id, ah.station_id, s.station_name,
                           s.region_id, r.region_name,
                           ah.observed_at, ah.temperature, ah.humidity,
                           ah.precipitation, ah.wind_speed, ah.wind_direction,
                           ah.apparent_temp, ah.heat_index,
                           ah.quality_flag, ah.collected_at
                    FROM   asos_history ah
                    JOIN   asos_station s ON s.station_id = ah.station_id
                    JOIN   region r ON r.region_id = s.region_id
                    WHERE  DATE(ah.observed_at) = %s
                      AND  ah.observed_at = (
                               SELECT MAX(ah2.observed_at)
                               FROM   asos_history ah2
                               WHERE  ah2.station_id = ah.station_id
                                 AND  DATE(ah2.observed_at) = %s
                           )
                    ORDER  BY ah.station_id ASC
                    """,
                    (today, today),
                )
            return cur.fetchall() or []
    except Exception as exc:
        logger.error(f"[today_data] get_today_asos_latest 오류: {exc}")
        return []


# ════════════════════════════════════════════════════════════════════
# operation_available_day 조회
# ════════════════════════════════════════════════════════════════════

def get_today_availability(region_id: Optional[int] = None) -> list[dict]:
    """
    오늘 날짜의 지역별 훈련 가능 여부를 조회한다.

    Parameters
    ----------
    region_id : int | None
        특정 지역 ID. None이면 전체 지역 조회.

    Returns
    -------
    list[dict]
        각 dict: id, region_id, region_name, target_date,
                 is_available, restriction_reason,
                 avg_apparent_temp, avg_heat_index, calculated_at
    """
    today = date.today().isoformat()
    try:
        with get_cursor() as (cur, _):
            if region_id is not None:
                cur.execute(
                    """
                    SELECT oad.id, oad.region_id, r.region_name,
                           oad.target_date, oad.is_available,
                           oad.restriction_reason,
                           oad.avg_apparent_temp, oad.avg_heat_index,
                           oad.calculated_at
                    FROM   operation_available_day oad
                    JOIN   region r ON r.region_id = oad.region_id
                    WHERE  oad.target_date = %s
                      AND  oad.region_id = %s
                    ORDER  BY oad.region_id ASC
                    """,
                    (today, region_id),
                )
            else:
                cur.execute(
                    """
                    SELECT oad.id, oad.region_id, r.region_name,
                           oad.target_date, oad.is_available,
                           oad.restriction_reason,
                           oad.avg_apparent_temp, oad.avg_heat_index,
                           oad.calculated_at
                    FROM   operation_available_day oad
                    JOIN   region r ON r.region_id = oad.region_id
                    WHERE  oad.target_date = %s
                    ORDER  BY oad.region_id ASC
                    """,
                    (today,),
                )
            return cur.fetchall() or []
    except Exception as exc:
        logger.error(f"[today_data] get_today_availability 오류: {exc}")
        return []


# ════════════════════════════════════════════════════════════════════
# 통합 요약 조회
# ════════════════════════════════════════════════════════════════════

def get_today_summary(region_id: Optional[int] = None) -> dict:
    """
    오늘 날씨 데이터 통합 요약을 반환한다.

    Parameters
    ----------
    region_id : int | None
        특정 지역 ID. None이면 전체 지역 요약.

    Returns
    -------
    dict
        {
          "date":         "YYYY-MM-DD",
          "forecast":     [...],   # get_today_forecast_latest() 결과
          "asos_latest":  [...],   # get_today_asos_latest() 결과
          "availability": [...],   # get_today_availability() 결과
          "stats": {
              "total_regions":     int,   # 전체 지역 수
              "available_regions": int,   # 훈련 가능 지역 수
              "avg_temp":          float | None,  # 평균 기온 (예보 기준)
              "avg_apparent_temp": float | None,  # 평균 체감온도 (예보 기준)
          }
        }
    """
    today_str = date.today().isoformat()

    forecast    = get_today_forecast_latest(region_id)
    asos_latest = get_today_asos_latest()
    availability = get_today_availability(region_id)

    # 통계 계산
    total_regions     = len(availability)
    available_regions = sum(1 for r in availability if r.get("is_available"))

    temps         = [r["tmp"]           for r in forecast if r.get("tmp")           is not None]
    apparent_temps = [r["apparent_temp"] for r in forecast if r.get("apparent_temp") is not None]

    avg_temp          = round(sum(temps) / len(temps), 1)          if temps          else None
    avg_apparent_temp = round(sum(apparent_temps) / len(apparent_temps), 1) if apparent_temps else None

    return {
        "date":         today_str,
        "forecast":     forecast,
        "asos_latest":  asos_latest,
        "availability": availability,
        "stats": {
            "total_regions":     total_regions,
            "available_regions": available_regions,
            "avg_temp":          avg_temp,
            "avg_apparent_temp": avg_apparent_temp,
        },
    }


# ════════════════════════════════════════════════════════════════════
# 지역별 현재 체감온도 단일 조회 (anomaly_detector 연동용)
# ════════════════════════════════════════════════════════════════════

def get_current_apparent_temp(region_id: int) -> Optional[float]:
    """
    특정 지역의 오늘 가장 최근 예보 체감온도를 반환한다.
    anomaly_detector.py 에서 DB 조회 시 사용한다.

    Parameters
    ----------
    region_id : int
        지역 ID

    Returns
    -------
    float | None
        체감온도 (°C). 데이터 없으면 None.
    """
    today = date.today().isoformat()
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT apparent_temp
                FROM   forecast_data
                WHERE  region_id = %s
                  AND  DATE(forecast_target_time) = %s
                ORDER  BY forecast_target_time DESC
                LIMIT  1
                """,
                (region_id, today),
            )
            row = cur.fetchone()
            if row and row["apparent_temp"] is not None:
                return float(row["apparent_temp"])
    except Exception as exc:
        logger.error(f"[today_data] get_current_apparent_temp 오류: {exc}")
    return None


def get_current_temperature(region_id: int) -> Optional[float]:
    """
    특정 지역의 오늘 가장 최근 예보 기온을 반환한다.

    Parameters
    ----------
    region_id : int
        지역 ID

    Returns
    -------
    float | None
        기온 (°C). 데이터 없으면 None.
    """
    today = date.today().isoformat()
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT tmp
                FROM   forecast_data
                WHERE  region_id = %s
                  AND  DATE(forecast_target_time) = %s
                ORDER  BY forecast_target_time DESC
                LIMIT  1
                """,
                (region_id, today),
            )
            row = cur.fetchone()
            if row and row["tmp"] is not None:
                return float(row["tmp"])
    except Exception as exc:
        logger.error(f"[today_data] get_current_temperature 오류: {exc}")
    return None
