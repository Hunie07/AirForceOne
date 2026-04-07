"""
utils/heatmap_ui_components.py
───────────────────────────────
히트맵 페이지 Streamlit UI 렌더링 함수 모음
각 함수는 특정 UI 블록 하나를 책임지며 st.* 호출을 포함합니다.
"""
from __future__ import annotations

import datetime
import calendar
import pandas as pd
import streamlit as st

from utils.heatmap.bar_graph_function_sp import ALL_YEARS, ALL_MONTHS, calculate_yearly_statistics
from utils.heatmap.config import (
    LOCATION_MAPPING, HOUR_OPTIONS, MONTH_SEASON,
    CRITERIA_DATA, ROW1_HEIGHT, ROW2_HEIGHT, SESSION_DEFAULTS,
)
from utils.heatmap.data import (
    find_consecutive_available_periods,
    build_blocked_dates,
    build_monthly_rows,
    build_daily_table_df,
)
from utils.heatmap.figures import (
    create_heatmap_figure,
    get_heatmap_image_bytes,
    create_daily_line_figure,
)


# ══════════════════════════════════════════════════════════════════════════════
# 세션 상태 초기화
# ══════════════════════════════════════════════════════════════════════════════

def init_session_state() -> None:
    """SESSION_DEFAULTS 기준으로 세션 상태를 초기화합니다."""
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════════════
# 헤더 컨테이너
# ══════════════════════════════════════════════════════════════════════════════

def render_header() -> None:
    """제목 / 통제기준 팝오버 / 산출식 팝오버를 포함한 헤더를 렌더링합니다."""
    with st.container(border=True):
        hc1, hc2, hc3 = st.columns([7, 1.5, 1.5], vertical_alignment="center")

        with hc1:
            st.subheader("▶ 연간 훈련가용 판정 현황", divider=False)
            st.caption("특정 연도의 1월~12월(365일) 체감온도 분석 / 군 훈련 가능 여부 기준 적용")

        with hc2:
            with st.popover("🚨 통제기준", use_container_width=True):
                st.markdown("#### 🌡️ 야외 훈련 통제 기준")
                st.table(pd.DataFrame(CRITERIA_DATA).set_index("구분"))

        with hc3:
            with st.popover("🧮 산출식", use_container_width=True):
                st.markdown("#### 🌡️ 온도지수(체감온도) 산출 공식")
                st.markdown("**❄️ 겨울철 (풍속 고려)** — 10월~4월 적용")
                st.latex(r"WCT = 13.12 + 0.6215\,T_a - 11.37\,V^{0.16} + 0.3965\,V^{0.16}\,T_a")
                st.caption("* Tₐ : 기온(°C)   * V : 지상 10m 풍속(km/h)")
                st.divider()
                st.markdown("**☀️ 여름철 (습도 고려)** — 5월~9월 적용 / ※ 보정치 +3.0 제외")
                st.latex(r"WCT = -0.2442 + 0.55399\,T_w + 0.45535\,T_a - 0.0022\,T_w^2 + 0.00278\,T_w\,T_a")
                st.caption("* Tₐ : 기온(°C)   * T_w : 습구온도(°C)")


# ══════════════════════════════════════════════════════════════════════════════
# 필터 바 (지역 / 연도 / 시간)
# ══════════════════════════════════════════════════════════════════════════════

def render_filter_bar(splocs: list[str]) -> None:
    """지역·연도·시간 필터 선택 행을 렌더링합니다. 변경 시 st.rerun() 호출."""
    st.write("")
    fc1, fc2, fc3, _ = st.columns([2, 2, 3, 3])

    with fc1:
        new_sploc = st.selectbox(
            "지역 (지점)", splocs,
            index=splocs.index(st.session_state.sel_sploc),
            format_func=lambda x: LOCATION_MAPPING.get(x, x),
            key="sploc_sel",
        )
        if new_sploc != st.session_state.sel_sploc:
            st.session_state.sel_sploc = new_sploc; st.rerun()

    with fc2:
        new_yr = st.selectbox(
            "연도", ALL_YEARS,
            index=ALL_YEARS.index(st.session_state.sel_year),
            key="yr_sel",
        )
        if new_yr != st.session_state.sel_year:
            st.session_state.sel_year = new_yr; st.rerun()

    with fc3:
        hr_idx = HOUR_OPTIONS.index(f"{str(st.session_state.sel_hour).zfill(2)}시")
        new_hr_str = st.segmented_control(
            "시간", HOUR_OPTIONS,
            default=HOUR_OPTIONS[hr_idx],
            key="hr_seg",
        )
        if new_hr_str:
            new_hr_int_str = str(int(new_hr_str.replace("시", "")))
            if new_hr_int_str != st.session_state.sel_hour:
                st.session_state.sel_hour = new_hr_int_str; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Row 1 — [1-1] 훈련 가용일수 종합
# ══════════════════════════════════════════════════════════════════════════════

def render_yearly_stats(df: pd.DataFrame) -> tuple[dict, dict]:
    """
    연간 종합 통계 블록을 렌더링합니다.
    월별 통계 딕셔너리 (m_normal, m_total) 를 반환해 Row 2에서 재사용합니다.
    """
    m_normal, m_total, y_stats = calculate_yearly_statistics(
        df,
        st.session_state.sel_sploc,
        st.session_state.sel_year,
        int(st.session_state.sel_hour),
    )
    with st.container(height=ROW1_HEIGHT, border=True):
        st.markdown("#### 📊 훈련 가용일수 종합")
        st.divider()
        st.metric("✅ 정상 (훈련 가용)", f"{y_stats['normal']}일",
                  delta=f"전체 {y_stats['total']}일 중", delta_color="off")
        st.metric("⚠️ 주의 (고온/한랭)",  f"{y_stats['caution']}일")
        st.metric("⛔ 부분제한 / 제한",   f"{y_stats['limit']}일")
        st.metric("🛑 전면 중지",         f"{y_stats['stop']}일")

    return m_normal, m_total


# ══════════════════════════════════════════════════════════════════════════════
# Row 1 — [1-2] 히트맵
# ══════════════════════════════════════════════════════════════════════════════

def render_heatmap(df: pd.DataFrame, disp_name: str) -> None:
    """히트맵 제목 + 이미지 저장 버튼 + Plotly 히트맵을 렌더링합니다."""
    with st.container(height=ROW1_HEIGHT, border=True):
        title_col, btn_col = st.columns([7, 2], vertical_alignment="center")

        with title_col:
            st.markdown(
                f"#### ▶ {st.session_state.sel_year}년 {disp_name} 일별 훈련가용 판정"
                f" ({st.session_state.sel_hour}시 기준)"
            )
        with btn_col:
            try:
                img_bytes = get_heatmap_image_bytes(
                    df, st.session_state.sel_sploc,
                    st.session_state.sel_year, st.session_state.sel_hour, disp_name,
                )
                dl_name = (
                    f"{disp_name}_{st.session_state.sel_year}년_"
                    f"{st.session_state.sel_hour}시_히트맵.png"
                )
                st.download_button(
                    label="💾 이미지 저장", data=img_bytes,
                    file_name=dl_name, mime="image/png", use_container_width=True,
                )
            except Exception:
                st.warning("⚠️ `pip install kaleido` 필요")

        fig = create_heatmap_figure(
            df, st.session_state.sel_sploc,
            st.session_state.sel_year, st.session_state.sel_hour, disp_name,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
# Row 1 — [1-3] 연속 가용 구간 추천
# ══════════════════════════════════════════════════════════════════════════════

def render_schedule_panel(df: pd.DataFrame) -> None:
    """훈련 일정 등록 / 차단 날짜 제외 / 연속 가용 구간 추천 블록을 렌더링합니다."""
    with st.container(height=ROW1_HEIGHT, border=True):
        st.markdown("#### 🎯 연속 가용 구간 추천")

        # 날짜 범위 입력
        year_val = st.session_state.sel_year
        date_range = st.date_input(
            "훈련 예정 기간 입력",
            value=(),
            min_value=datetime.date(year_val, 1, 1),
            max_value=datetime.date(year_val, 12, 31),
            help="시작일과 종료일을 드래그해서 선택하세요.",
            key="schedule_range",
        )

        add_col, clear_col = st.columns(2)
        with add_col:
            if st.button("➕ 일정 등록", use_container_width=True):
                if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                    label = (
                        f"{date_range[0].month}월 {date_range[0].day}일"
                        f" ~ {date_range[1].month}월 {date_range[1].day}일"
                    )
                    st.session_state.blocked_schedules.append(
                        {"label": label, "start": date_range[0], "end": date_range[1]}
                    )
                else:
                    st.warning("시작일과 종료일을 모두 선택해주세요.")
        with clear_col:
            if st.button("🗑 전체 삭제", use_container_width=True):
                st.session_state.blocked_schedules = []; st.rerun()

        # 등록된 일정 expander
        sched_count = len(st.session_state.blocked_schedules)
        with st.expander(f"📋 등록된 훈련 일정 ({sched_count}건)", expanded=sched_count > 0):
            if sched_count == 0:
                st.caption("등록된 일정이 없습니다.")
            else:
                for idx, sched in enumerate(st.session_state.blocked_schedules):
                    col_lbl, col_del = st.columns([4, 1])
                    with col_lbl:
                        st.write(f"📌 {sched['label']}")
                    with col_del:
                        if st.button("삭제", key=f"del_sched_{idx}", use_container_width=True):
                            st.session_state.blocked_schedules.pop(idx); st.rerun()

        # 탐색 옵션 + 결과
        min_days = st.number_input(
            "최소 연속일수", min_value=2, max_value=30, value=5, step=1,
            help="이 일수 이상 연속으로 훈련 가능한 구간을 탐색합니다.",
        )
        top_n = st.number_input("상위 추천 개수", min_value=1, max_value=10, value=5, step=1)

        blocked_set = build_blocked_dates(st.session_state.blocked_schedules)
        periods = find_consecutive_available_periods(
            df, st.session_state.sel_sploc, st.session_state.sel_year,
            int(st.session_state.sel_hour),
            min_days=int(min_days), top_n=int(top_n),
            blocked_dates=blocked_set,
        )

        if periods:
            if blocked_set:
                st.caption(f"※ 등록된 훈련 일정 {sched_count}건 제외 후 탐색")
            rows = [
                {
                    "순위":    f"{rank}위",
                    "구간":    f"{MONTH_SEASON.get(p['시작월'], '')} {p['시작']} ~ {p['종료']}",
                    "연속일수": f"{p['연속일수']}일",
                }
                for rank, p in enumerate(periods, start=1)
            ]
            st.dataframe(
                pd.DataFrame(rows), hide_index=True, use_container_width=True,
                column_config={
                    "순위":    st.column_config.TextColumn("순위",    width="small"),
                    "구간":    st.column_config.TextColumn("구간",    width="medium"),
                    "연속일수": st.column_config.TextColumn("연속일수", width="small"),
                },
            )
        else:
            st.info(f"{int(min_days)}일 이상 연속 가용 구간이 없습니다.")


# ══════════════════════════════════════════════════════════════════════════════
# Row 2 — [2-1] 월별 훈련 가용일수
# ══════════════════════════════════════════════════════════════════════════════

def render_monthly_table(m_normal: dict, m_total: dict) -> None:
    """월별 훈련 가용일수 테이블을 렌더링합니다."""
    with st.container(height=ROW2_HEIGHT, border=True):
        st.markdown("#### 📅 월별 훈련 가용일수")
        st.dataframe(
            pd.DataFrame(build_monthly_rows(m_normal, m_total)),
            hide_index=True, use_container_width=True,
            column_config={
                "월":     st.column_config.TextColumn("월",     width="small"),
                "가용일수": st.column_config.TextColumn("가용일수", width="small"),
                "비율":   st.column_config.TextColumn("비율",   width="small"),
            },
        )


# ══════════════════════════════════════════════════════════════════════════════
# Row 2 — [2-2] 일별 기상 상세 조회
# ══════════════════════════════════════════════════════════════════════════════

def render_daily_detail(df: pd.DataFrame) -> None:
    """월/일 선택 → 24시간 라인 플롯 + 상세 테이블을 렌더링합니다."""
    with st.container(height=ROW2_HEIGHT, border=True):
        st.markdown("#### 🔍 일별 기상 상세 조회")

        sel_c1, sel_c2 = st.columns(2)
        with sel_c1:
            new_m = st.selectbox(
                "월", ALL_MONTHS,
                index=ALL_MONTHS.index(st.session_state.card_m),
                format_func=lambda x: f"{x}월", key="s_m",
            )
            if new_m != st.session_state.card_m:
                st.session_state.card_m = new_m; st.rerun()
        with sel_c2:
            max_days = calendar.monthrange(
                int(st.session_state.sel_year), st.session_state.card_m
            )[1]
            if st.session_state.card_d > max_days:
                st.session_state.card_d = max_days
            new_d = st.selectbox(
                "일", list(range(1, max_days + 1)),
                index=st.session_state.card_d - 1,
                format_func=lambda x: f"{x}일", key="s_d",
            )
            if new_d != st.session_state.card_d:
                st.session_state.card_d = new_d; st.rerun()

        day_df = df[
            (df["year"]   == st.session_state.sel_year)
            & (df["month"] == st.session_state.card_m)
            & (df["day"]   == st.session_state.card_d)
            & (df["sploc"] == st.session_state.sel_sploc)
        ].sort_values("hour")

        if day_df.empty:
            st.warning("선택하신 날짜의 24시간 데이터가 없습니다.")
            return

        # 라인 플롯
        st.plotly_chart(
            create_daily_line_figure(day_df),
            use_container_width=True, config={"displayModeBar": False},
        )

        # 상세 테이블
        st.dataframe(
            build_daily_table_df(day_df),
            hide_index=True, use_container_width=True, height=480,
            column_config={
                "시간":     st.column_config.TextColumn("시간",     width="small"),
                "체감(°C)": st.column_config.NumberColumn("체감(°C)", format="%.1f",  width="small"),
                "기온":     st.column_config.NumberColumn("기온",     format="%.1f",  width="small"),
                "풍속":     st.column_config.NumberColumn("풍속",     format="%.1f",  width="small"),
                "습도":     st.column_config.NumberColumn("습도",     format="%.0f%%", width="small"),
                "강수":     st.column_config.NumberColumn("강수",     format="%.1f",  width="small"),
                "적설":     st.column_config.NumberColumn("적설",     format="%.1f",  width="small"),
            },
        )
        st.caption("데이터 기준: 기상청 AOS")
