# -*- coding: utf-8 -*-
"""
🏘️ 동네별 인구 피라미드 (Streamlit 앱)

- 데이터: 2015~2026년 전국 읍·면·동 연령별·성별 인구 (압축된 CSV)
- 가장 최신 연도(2026년)만 골라서 사용합니다.
- 시도 → 시군구 → 동 순서로 고르면, 그 동네의 인구 피라미드를 그려 줍니다.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────
# 1. 기본 설정 (바꾸고 싶은 값은 여기에 모아 두었어요)
# ──────────────────────────────────────────────

# 데이터 주소 (.zip 압축 파일이지만 pandas가 바로 읽어 줍니다)
DATA_URL = (
    "https://raw.githubusercontent.com/Yyeon222/dashboard/"
    "main/population_ts_yearly_gender.zip"
)

# 나이 라벨: 0세 ~ 99세, 그리고 맨 마지막 '100세 이상'
# 이 리스트의 순서가 그대로 세로축 순서가 됩니다 (아래 0세, 위 100세 이상)
AGE_LABELS = [f"{age}세" for age in range(100)] + ["100세 이상"]

# 데이터 표의 열 이름 (예: '남_0세', '여_100세 이상')
MALE_COLS = [f"남_{label}" for label in AGE_LABELS]
FEMALE_COLS = [f"여_{label}" for label in AGE_LABELS]

# 시군구가 비어 있는 곳(예: 세종특별자치시)에 붙일 이름
NO_SIGUNGU = "(시군구 없음)"

# 65세 이상 비율을 계산할 때 쓰는 시작 나이
SENIOR_START = 65

# 따뜻한 톤의 색깔
MALE_COLOR = "#C8553D"    # 벽돌색 (남자)
FEMALE_COLOR = "#F4A259"  # 꿀색 (여자)
PAPER_COLOR = "#FFF8F0"   # 바깥 배경 (크림색)
PLOT_COLOR = "#FFFDF9"    # 그래프 안쪽 배경


# ──────────────────────────────────────────────
# 2. 데이터 불러오기
# ──────────────────────────────────────────────

# @st.cache_data: 한 번 읽은 데이터는 저장해 두고 재사용해서 앱이 빨라집니다
@st.cache_data(show_spinner="인구 데이터를 불러오는 중이에요 ☕")
def load_latest_population():
    """전국 데이터를 읽고, 가장 최신 연도의 행만 돌려줍니다."""
    raw = pd.read_csv(DATA_URL)  # 압축 파일도 그대로 읽힙니다

    latest_year = int(raw["연도"].max())  # 가장 큰 연도 = 최신 연도
    df = raw[raw["연도"] == latest_year].copy()

    # 시군구가 비어 있는 행에 이름을 붙여서 드롭다운에서 고를 수 있게 합니다
    df["시군구"] = df["시군구"].fillna(NO_SIGUNGU)

    return df, latest_year


# ──────────────────────────────────────────────
# 3. 그래프 그리기
# ──────────────────────────────────────────────

def make_tick_setup(max_value):
    """가로축 눈금 위치와 글자를 정합니다. 음수 쪽도 양수처럼 보이게 글자만 바꿉니다."""
    # 눈금 간격: 최댓값의 1/4을 10의 거듭제곱으로 맞춥니다 (예: 375 → 100)
    rough_step = max(max_value / 4, 1)
    step = 10 ** int(np.floor(np.log10(rough_step)))

    # 한쪽으로 몇 칸이 필요한지 (최댓값을 넘을 때까지 올림)
    n_steps = int(np.ceil(max_value / step))
    tick_values = [i * step for i in range(-n_steps, n_steps + 1)]
    tick_texts = [f"{abs(v):,}" for v in tick_values]  # 글자는 절댓값으로
    return tick_values, tick_texts


def make_pyramid(males, females, place_name, year):
    """남녀 인구 배열을 받아서 가로 막대 인구 피라미드를 만듭니다."""
    # 가장 많은 사람 수 (그래프 범위를 정하는 데 씁니다, 최소 1)
    max_value = int(max(males.max(), females.max(), 1))

    fig = go.Figure()

    # 남자: 값을 음수로 바꿔서 가운데 0을 기준으로 왼쪽에 그립니다
    fig.add_trace(go.Bar(
        y=AGE_LABELS,
        x=-males,
        orientation="h",
        name="남자",
        marker_color=MALE_COLOR,
        customdata=males,  # 마우스를 올렸을 때 보여 줄 실제 인원 수
        hovertemplate="%{y}<br>남자 %{customdata:,}명<extra></extra>",
    ))

    # 여자: 양수 그대로 오른쪽에 그립니다
    fig.add_trace(go.Bar(
        y=AGE_LABELS,
        x=females,
        orientation="h",
        name="여자",
        marker_color=FEMALE_COLOR,
        hovertemplate="%{y}<br>여자 %{x:,}명<extra></extra>",
    ))

    tick_values, tick_texts = make_tick_setup(max_value)

    fig.update_layout(
        title=f"{place_name} 인구 피라미드 ({year}년)",
        barmode="overlay",  # 남녀 막대는 왼쪽/오른쪽으로 갈라져 있어서 겹치지 않아요
        bargap=0.1,
        height=800,
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.05),
        margin=dict(l=20, r=20, t=90, b=20),
    )

    # 가로축(인구 수): 가운데 0을 기준으로 좌우 대칭 범위
    fig.update_xaxes(
        title_text="인구 (명)",
        range=[-max_value * 1.1, max_value * 1.1],
        tickvals=tick_values,
        ticktext=tick_texts,
        zeroline=True,
        zerolinecolor="#8C7B6B",
    )

    # 세로축(나이): 0세가 맨 아래, 100세 이상이 맨 위
    # categoryarray로 나이 순서를 고정합니다. (축 뒤집기나 값 크기순 정렬은 쓰지 않아요)
    fig.update_yaxes(
        title_text="나이",
        type="category",
        categoryorder="array",
        categoryarray=AGE_LABELS,
        tickmode="array",
        tickvals=AGE_LABELS[::5],  # 5살 간격으로만 글자 표시 (0세, 5세, ... 100세 이상)
        automargin=True,
    )
    return fig


# ──────────────────────────────────────────────
# 4. 화면 구성
# ──────────────────────────────────────────────

st.set_page_config(page_title="동네별 인구 피라미드", page_icon="🏘️", layout="wide")

st.title("🏘️ 동네별 인구 피라미드")
st.write("시도 → 시군구 → 동 순서로 골라 보세요. 왼쪽은 남자, 오른쪽은 여자예요.")

df, latest_year = load_latest_population()
st.caption(f"기준 연도: {latest_year}년 (전국 읍·면·동 연령별 인구)")

# 드롭다운 3개를 한 줄에 나란히 놓습니다 (폰에서는 자동으로 세로로 쌓여요)
col_sido, col_sigungu, col_dong = st.columns(3)

with col_sido:
    # 시도 목록 (가나다순)
    sido = st.selectbox("시도", sorted(df["시도"].unique()))

with col_sigungu:
    # 고른 시도 안에 있는 시군구만 보여 줍니다
    sigungu_list = sorted(df.loc[df["시도"] == sido, "시군구"].unique())
    sigungu = st.selectbox("시군구", sigungu_list)

with col_dong:
    # 고른 시도·시군구 안에 있는 동만 보여 줍니다
    dong_list = sorted(
        df.loc[(df["시도"] == sido) & (df["시군구"] == sigungu), "동"].unique()
    )
    dong = st.selectbox("동", dong_list)

# 고른 동네의 한 줄(행)만 꺼내기 (같은 시도·시군구·동은 한 줄뿐이에요)
row = df[
    (df["시도"] == sido) & (df["시군구"] == sigungu) & (df["동"] == dong)
].iloc[0]

# 0세~100세 이상 인구 수를 숫자 배열로 꺼냅니다
males = row[MALE_COLS].to_numpy(dtype=np.int64)
females = row[FEMALE_COLS].to_numpy(dtype=np.int64)

# 요약 숫자 계산
total = int(males.sum() + females.sum())
senior = int(males[SENIOR_START:].sum() + females[SENIOR_START:].sum())
senior_ratio = senior / total * 100 if total > 0 else 0

# 시군구 이름이 '(시군구 없음)'이면 제목에서 빼 줍니다
place_name = " ".join(name for name in [sido, sigungu, dong] if name != NO_SIGUNGU)

# 요약 카드 4개
m1, m2, m3, m4 = st.columns(4)
m1.metric("전체 인구", f"{total:,}명")
m2.metric("남자", f"{int(males.sum()):,}명")
m3.metric("여자", f"{int(females.sum()):,}명")
m4.metric(f"{SENIOR_START}세 이상 비율", f"{senior_ratio:.1f}%")

# 인구 피라미드 그리기
fig = make_pyramid(males, females, place_name, latest_year)
st.plotly_chart(fig, width="stretch")

st.caption("세로축: 맨 아래가 0세, 위로 갈수록 나이가 많고 맨 위가 100세 이상이에요.")
