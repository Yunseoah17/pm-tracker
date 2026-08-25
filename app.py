import streamlit as st
import pandas as pd
import math
import requests
import pydeck as pdk
from datetime import date, timedelta


# ==========================================
# 기본 설정
# ==========================================

st.set_page_config(
    page_title="PM TRACKER",
    page_icon="🌫️",
    layout="wide"
)


# ==========================================
# 지역 데이터
# ==========================================

LOCATIONS = {
    "서울": {
        "stations": {
            "서울 ○○ 측정소": (37.5665, 126.9780),
            "서울 강남 측정소": (37.5172, 127.0473),
            "서울 마포 측정소": (37.5663, 126.9014)
        }
    },
    "인천": {
        "stations": {
            "인천 ○○ 측정소": (37.4563, 126.7052),
            "인천 남동 측정소": (37.4475, 126.7314)
        }
    },
    "수원": {
        "stations": {
            "수원 ○○ 측정소": (37.2636, 127.0286),
            "수원 영통 측정소": (37.2596, 127.0466)
        }
    }
}


# ==========================================
# 풍향 변환
# ==========================================

def wind_direction_text(degree):

    directions = [
        "북풍",
        "북북동풍",
        "북동풍",
        "동북동풍",
        "동풍",
        "동남동풍",
        "남동풍",
        "남남동풍",
        "남풍",
        "남남서풍",
        "남서풍",
        "서남서풍",
        "서풍",
        "서북서풍",
        "북서풍",
        "북북서풍"
    ]

    index = int((degree + 11.25) / 22.5) % 16

    return directions[index]


# ==========================================
# 실제 기상 데이터
# ==========================================

def get_weather(lat, lon, selected_date, selected_hour):

    today = date.today()

    if selected_date >= today - timedelta(days=7):

        url = "https://api.open-meteo.com/v1/forecast"

    else:

        url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "temperature_2m,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "surface_pressure"
        ),
        "timezone": "Asia/Seoul",
        "start_date": selected_date.strftime("%Y-%m-%d"),
        "end_date": selected_date.strftime("%Y-%m-%d")
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        hourly = data["hourly"]

        target_time = (
            f"{selected_date.strftime('%Y-%m-%d')}"
            f"T{selected_hour:02d}:00"
        )

        if target_time not in hourly["time"]:
            return None

        i = hourly["time"].index(target_time)

        return {
            "temperature": hourly["temperature_2m"][i],
            "wind_speed": hourly["wind_speed_10m"][i],
            "wind_direction": hourly["wind_direction_10m"][i],
            "pressure": hourly["surface_pressure"][i]
        }

    except Exception as e:

        return {
            "error": str(e)
        }


# ==========================================
# 역추적 경로 계산
# ==========================================

def calculate_backward_path(
    lat,
    lon,
    wind_direction,
    wind_speed,
    hours=5
):

    points = []

    current_lat = lat
    current_lon = lon

    points.append(
        [current_lon, current_lat]
    )

    # 바람이 불어오는 방향을 따라
    # 과거 발생원을 추정
    bearing = math.radians(wind_direction)

    for h in range(1, hours + 1):

        distance = wind_speed * 3.6 * h

        delta_lat = (
            distance * math.cos(bearing)
        ) / 111

        delta_lon = (
            distance * math.sin(bearing)
        ) / (
            111 *
            math.cos(math.radians(lat))
        )

        new_lat = lat + delta_lat
        new_lon = lon + delta_lon

        points.append(
            [new_lon, new_lat]
        )

    return points


# ==========================================
# 발생원 후보
# ==========================================

def generate_sources(
    lat,
    lon,
    wind_direction
):

    candidates = [

        {
            "name": "산업시설 A",
            "type": "산업 배출",
            "lat": lat + 0.08,
            "lon": lon - 0.05
        },

        {
            "name": "주요도로 B",
            "type": "교통 배출",
            "lat": lat - 0.05,
            "lon": lon + 0.08
        },

        {
            "name": "공사장 C",
            "type": "비산먼지",
            "lat": lat + 0.04,
            "lon": lon + 0.06
        }

    ]

    for source in candidates:

        dy = source["lat"] - lat

        dx = (
            source["lon"] - lon
        ) * math.cos(
            math.radians(lat)
        )

        angle = math.degrees(
            math.atan2(dx, dy)
        )

        if angle < 0:
            angle += 360

        diff = abs(
            angle - wind_direction
        )

        if diff > 180:
            diff = 360 - diff

        score = max(
            0,
            100 - diff * 1.4
        )

        source["score"] = round(score)

    return sorted(
        candidates,
        key=lambda x: x["score"],
        reverse=True
    )


# ==========================================
# CSS
# ==========================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 44px;
        font-weight: 900;
        letter-spacing: 3px;
    }

    .subtitle {
        color: #8f9bad;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .section-title {
        color: #91a4bd;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    .source-card {
        background: #111925;
        border: 1px solid #283548;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .source-title {
        font-size: 19px;
        font-weight: 800;
    }

    .source-type {
        color: #8f9bad;
        font-size: 14px;
        margin-top: 4px;
    }

    .score {
        font-size: 30px;
        font-weight: 900;
        margin-top: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================
# 사이드바
# ==========================================

st.sidebar.markdown(
    "## ANALYSIS SETTINGS"
)

region = st.sidebar.selectbox(
    "분석 지역",
    list(LOCATIONS.keys())
)

station_name = st.sidebar.selectbox(
    "측정소",
    list(
        LOCATIONS[region]["stations"].keys()
    )
)

station_lat, station_lon = (
    LOCATIONS[region]["stations"][station_name]
)

selected_date = st.sidebar.date_input(
    "분석 날짜",
    value=date.today()
)

selected_hour = st.sidebar.selectbox(
    "분석 시간",
    list(range(24)),
    index=9,
    format_func=lambda x: f"{x:02d}:00"
)

tracking_range = st.sidebar.slider(
    "역추적 범위",
    5,
    50,
    15,
    5
)

start_button = st.sidebar.button(
    "🔍 발생원 추적 시작",
    use_container_width=True
)


# ==========================================
# 제목
# ==========================================

st.markdown(
    '<div class="main-title">PM TRACKER</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '미세먼지 발생원 역추적 시스템'
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# 시작 전 화면
# ==========================================

if not start_button:

    st.markdown(
        '<div class="section-title">SYSTEM READY</div>',
        unsafe_allow_html=True
    )

    st.info(
        "왼쪽에서 분석 조건을 설정한 뒤 "
        "'발생원 추적 시작'을 눌러주세요."
    )

    st.markdown(
        "## 🌫️ 미세먼지는 어디에서 왔을까?"
    )

    st.write(
        "측정 지점의 기상 데이터를 분석하여 "
        "미세먼지가 이동해 온 방향을 역추적합니다."
    )

    st.markdown(
        "### 분석 과정"
    )

    st.write(
        "대기질 데이터 → 풍향·풍속 분석 → "
        "역추적 경로 계산 → 발생원 후보 비교"
    )

    st.stop()


# ==========================================
# 기상 데이터 불러오기
# ==========================================

with st.spinner(
    "실제 기상 데이터를 불러오는 중..."
):

    weather = get_weather(
        station_lat,
        station_lon,
        selected_date,
        selected_hour
    )


if weather is None:

    st.error(
        "선택한 시간의 기상 데이터를 찾지 못했습니다."
    )

    st.stop()


if "error" in weather:

    st.error(
        "기상 데이터를 불러오는 과정에서 오류가 발생했습니다."
    )

    st.stop()


temperature = weather["temperature"]

wind_speed = weather["wind_speed"]

wind_direction = weather["wind_direction"]

pressure = weather["pressure"]

direction_text = wind_direction_text(
    wind_direction
)

estimated_distance = (
    wind_speed * 3.6
)


# ==========================================
# 대기 분석
# ==========================================

st.markdown(
    '<div class="section-title">'
    'ATMOSPHERIC ANALYSIS'
    '</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "기온",
        f"{temperature:.1f} °C"
    )

with c2:
    st.metric(
        "풍향",
        direction_text
    )

with c3:
    st.metric(
        "풍속",
        f"{wind_speed:.1f} m/s"
    )

with c4:
    st.metric(
        "1시간 예상 이동거리",
        f"{estimated_distance:.1f} km"
    )


st.divider()


# ==========================================
# 역추적 경로
# ==========================================

st.markdown(
    '<div class="section-title">'
    'BACKWARD TRAJECTORY MAP'
    '</div>',
    unsafe_allow_html=True
)

trajectory = calculate_backward_path(
    station_lat,
    station_lon,
    wind_direction,
    wind_speed,
    hours=5
)


# ==========================================
# 발생원 후보 계산
# ==========================================

sources = generate_sources(
    station_lat,
    station_lon,
    wind_direction
)


# ==========================================
# 지도용 데이터
# ==========================================

path_data = [
    {
        "path": trajectory
    }
]

station_data = [
    {
        "lon": station_lon,
        "lat": station_lat,
        "name": station_name
    }
]

source_data = []

for source in sources:

    source_data.append(
        {
            "lon": source["lon"],
            "lat": source["lat"],
            "name": source["name"],
            "score": source["score"]
        }
    )


# ==========================================
# PyDeck 지도
# ==========================================

path_layer = pdk.Layer(
    "PathLayer",
    data=path_data,
    get_path="path",
    get_width=7,
    get_color=[255, 90, 90],
    width_min_pixels=5
)


station_layer = pdk.Layer(
    "ScatterplotLayer",
    data=station_data,
    get_position="[lon, lat]",
    get_radius=900,
    get_fill_color=[30, 130, 255],
    pickable=True
)


source_layer = pdk.Layer(
    "ScatterplotLayer",
    data=source_data,
    get_position="[lon, lat]",
    get_radius=650,
    get_fill_color=[255, 80, 80],
    pickable=True
)


view_state = pdk.ViewState(
    latitude=station_lat,
    longitude=station_lon,
    zoom=9.5,
    pitch=0
)


deck = pdk.Deck(
    layers=[
        path_layer,
        station_layer,
        source_layer
    ],
    initial_view_state=view_state,
    tooltip={
        "html":
        "<b>{name}</b><br/>"
        "가능성: {score}점",
        "style": {
            "backgroundColor": "#111925",
            "color": "white"
        }
    }
)


st.pydeck_chart(
    deck,
    use_container_width=True
)


st.caption(
    "🔵 파란색 = 측정소   "
    "🔴 빨간색 = 발생원 후보   "
    "━━ 역추적 예상 경로"
)


# ==========================================
# 발생원 분석
# ==========================================

st.markdown(
    '<div class="section-title">'
    'SOURCE PROBABILITY'
    '</div>',
    unsafe_allow_html=True
)


for i, source in enumerate(
    sources,
    start=1
):

    st.markdown(
        f"""
<div class="source-card">
<div class="source-title">
{i}. {source["name"]}
</div>
<div class="source-type">
{source["type"]}
</div>
<div class="score">
{source["score"]}점
</div>
</div>
""",
        unsafe_allow_html=True
    )


# ==========================================
# 분석 정보
# ==========================================

st.divider()

st.markdown(
    "### 현재 분석 조건"
)

st.write(
    f"""
- 지역: **{region}**
- 측정소: **{station_name}**
- 분석 시각: **{selected_date} {selected_hour:02d}:00**
- 풍향: **{wind_direction:.0f}° ({direction_text})**
- 풍속: **{wind_speed:.1f} m/s**
- 기압: **{pressure:.0f} hPa**
"""
)

st.caption(
    "※ 현재 발생원 후보는 교육용 예시 데이터입니다. "
    "기상 데이터는 실제 데이터를 사용합니다."
)
