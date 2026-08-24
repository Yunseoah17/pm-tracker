import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# ─────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────

st.set_page_config(
    page_title="PM TRACKER",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────
# 디자인
# ─────────────────────────────────────

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: #080b10;
    color: #f1f5f9;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 0;
}

.sub-title {
    color: #8b98a8;
    font-size: 0.95rem;
    margin-top: 3px;
}

.system-status {
    text-align: right;
    color: #55d68a;
    font-size: 0.85rem;
    font-weight: 600;
}

.section-title {
    color: #94a3b8;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}

.metric-box {
    background: #111720;
    border: 1px solid #202a36;
    border-radius: 12px;
    padding: 18px;
    height: 115px;
}

.metric-label {
    color: #7f8c9d;
    font-size: 0.78rem;
}

.metric-value {
    font-size: 1.55rem;
    font-weight: 700;
    margin-top: 8px;
}

.result-card {
    background: #111720;
    border: 1px solid #202a36;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 10px;
}

.source-name {
    font-size: 1rem;
    font-weight: 700;
}

.source-score {
    font-size: 1.4rem;
    font-weight: 800;
}

.small-text {
    color: #8793a3;
    font-size: 0.78rem;
}

hr {
    border-color: #202a36;
}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# 데이터
# ─────────────────────────────────────

sources = pd.DataFrame({
    "발생원": [
        "산업시설 A",
        "주요도로 B",
        "산업시설 C",
        "발전시설 D"
    ],
    "종류": [
        "산업 배출",
        "교통 배출",
        "산업 배출",
        "발전시설"
    ],
    "위도": [
        37.505,
        37.535,
        37.555,
        37.475
    ],
    "경도": [
        126.920,
        126.955,
        126.985,
        126.935
    ],
    "점수": [
        82,
        57,
        43,
        31
    ]
})

station_lat = 37.517
station_lon = 126.970

# ─────────────────────────────────────
# 헤더
# ─────────────────────────────────────

header1, header2 = st.columns([4, 1])

with header1:
    st.markdown(
        '<div class="main-title">PM TRACKER</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">미세먼지 발생원 역추적 시스템</div>',
        unsafe_allow_html=True
    )

with header2:
    st.markdown(
        '<div class="system-status">● SYSTEM ONLINE</div>',
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────
# 분석 설정
# ─────────────────────────────────────

with st.sidebar:

    st.markdown(
        '<div class="section-title">ANALYSIS SETTINGS</div>',
        unsafe_allow_html=True
    )

    region = st.selectbox(
        "분석 지역",
        ["서울", "인천", "경기"]
    )

    station = st.selectbox(
        "측정소",
        ["서울 ○○ 측정소", "서울 △△ 측정소"]
    )

    date = st.date_input(
        "분석 날짜"
    )

    time = st.selectbox(
        "분석 시간",
        ["09:00", "12:00", "14:00", "16:00", "18:00"]
    )

    radius = st.slider(
        "역추적 범위",
        5,
        30,
        15,
        1,
        format="%d km"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    analyze = st.button(
        "🔍  발생원 추적 시작",
        use_container_width=True,
        type="primary"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.caption(
        "※ 현재 버전은 교육용 시뮬레이션 데이터로 작동합니다."
    )

# ─────────────────────────────────────
# 분석 결과
# ─────────────────────────────────────

if analyze:

    # 예시 분석값
    pm25 = 48
    wind_speed = 4.2
    wind_direction = 270

    # 풍향 텍스트
    direction_text = "서풍"

    # 이동거리
    travel_distance = wind_speed * 3600 / 1000

    # 점수순 정렬
    ranked = sources.sort_values(
        "점수",
        ascending=False
    ).reset_index(drop=True)

    # ─────────────────────────────────
    # 상단 지표
    # ─────────────────────────────────

    st.markdown(
        '<div class="section-title">ATMOSPHERIC ANALYSIS</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">PM2.5 농도</div>
            <div class="metric-value">{pm25} μg/m³</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">풍향</div>
            <div class="metric-value">← {direction_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">풍속</div>
            <div class="metric-value">{wind_speed} m/s</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">예상 이동거리 / 1시간</div>
            <div class="metric-value">{travel_distance:.1f} km</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────
    # 지도 + 결과
    # ─────────────────────────────────

    left, right = st.columns([2.3, 1])

    with left:

        st.markdown(
            '<div class="section-title">BACKWARD TRAJECTORY MAP</div>',
            unsafe_allow_html=True
        )

        # 역추적 경로
        trajectory_lat = [
            station_lat,
            37.525,
            37.535,
            37.545,
            37.555
        ]

        trajectory_lon = [
            station_lon,
            126.955,
            126.940,
            126.925,
            126.910
        ]

        fig = go.Figure()

        # 역추적 선
        fig.add_trace(
            go.Scattermapbox(
                lat=trajectory_lat,
                lon=trajectory_lon,
                mode="lines+markers",
                line=dict(
                    width=4
                ),
                marker=dict(
                    size=7
                ),
                name="역추적 경로"
            )
        )

        # 측정소
        fig.add_trace(
            go.Scattermapbox(
                lat=[station_lat],
                lon=[station_lon],
                mode="markers",
                marker=dict(
                    size=18
                ),
                text=["현재 측정소"],
                name="측정소"
            )
        )

        # 발생원
        fig.add_trace(
            go.Scattermapbox(
                lat=sources["위도"],
                lon=sources["경도"],
                mode="markers+text",
                marker=dict(
                    size=12
                ),
                text=sources["발생원"],
                textposition="top center",
                name="발생원 후보"
            )
        )

        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(
                    lat=station_lat,
                    lon=station_lon
                ),
                zoom=10.5
            ),
            height=560,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#080b10",
            plot_bgcolor="#080b10",
            legend=dict(
                bgcolor="rgba(10,14,20,0.85)"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.markdown(
            '<div class="section-title">SOURCE PROBABILITY</div>',
            unsafe_allow_html=True
        )

        for i, row in ranked.iterrows():

            st.markdown(f"""
            <div class="result-card">
                <div class="source-name">
                    {i+1}. {row['발생원']}
                </div>

                <div class="small-text">
                    {row['종류']}
                </div>

                <div class="source-score">
                    {row['점수']}점
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            '<div class="section-title">CHEMICAL FINGERPRINT</div>',
            unsafe_allow_html=True
        )

        st.markdown("""
        <div class="result-card">

        <div class="small-text">황산염 계열</div>
        ████████████  높음

        <br><br>

        <div class="small-text">질산염 계열</div>
        ████████  중간

        <br><br>

        <div class="small-text">금속성분</div>
        ██████████  높음

        <br><br>

        <b>→ 산업 배출 특성과 높은 유사성</b>

        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────
    # 분석 설명
    # ─────────────────────────────────

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">ANALYSIS SUMMARY</div>',
        unsafe_allow_html=True
    )

    st.info(
        f"관측 지점의 풍향은 {direction_text}({wind_direction}°)으로 "
        f"분석되었습니다. 풍속 {wind_speed} m/s 조건에서 "
        f"공기 흐름을 역방향으로 추적하여 주변 발생원 후보를 계산했습니다."
    )

    st.caption(
        "※ 발생원 점수는 풍향·풍속·거리·화학적 특성을 단순화한 "
        "교육용 추정 모델입니다. 실제 배출 기여율을 의미하지 않습니다."
    )

else:

    # 시작 전 화면
    st.markdown(
        '<div class="section-title">SYSTEM READY</div>',
        unsafe_allow_html=True
    )

    st.info(
        "왼쪽의 분석 조건을 설정한 뒤 「발생원 추적 시작」 버튼을 눌러주세요."
    )

    st.markdown("""
    ### 🌫️ 미세먼지는 어디에서 왔을까?

    PM TRACKER는 **대기질 데이터와 기상 데이터를 결합하여
    미세먼지의 이동 경로를 역추적하는 교육용 분석 시스템**입니다.

    **분석 과정**

    `대기질 데이터`
    → `풍향·풍속 분석`
    → `역추적 경로 계산`
    → `주변 발생원 탐색`
    → `발생원 가능성 산출`
    """)

st.markdown("---")

st.markdown(
    "<div style='text-align:center; color:#64748b; font-size:0.75rem;'>"
    "PM TRACKER · Educational Air Pollution Source Tracking System"
    "</div>",
    unsafe_allow_html=True
)
