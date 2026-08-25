import streamlit as st
import pandas as pd
import math
import requests
from datetime import date, timedelta

st.set_page_config(
    page_title="PM TRACKER",
    page_icon="🌫️",
    layout="wide"
)

# -----------------------------
# 기본 설정
# -----------------------------

st.markdown("""
<style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: 2px;
    }

    .subtitle {
        color: #9aa4b2;
        font-size: 17px;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #8fa1b8;
        margin-top: 20px;
    }

    .result-box {
        padding: 18px;
        border-radius: 12px;
        background: #111925;
        border: 1px solid #263244;
        margin-bottom: 12px;
    }

    .source-name {
        font-size: 18px;
        font-weight: 700;
    }

    .source-score {
        font-size: 30px;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 지역 / 측정소
# -----------------------------

LOCATIONS = {
    "서울": {
        "lat": 37.5665,
        "lon": 126.9780,
        "stations": {
            "서울 ○○ 측정소": (37.5665, 126.9780),
            "서울 강남 측정소": (37.5172, 127.0473),
            "서울 마포 측정소": (37.5663, 126.9014)
        }
    },
    "인천": {
        "lat": 37.4563,
        "lon": 126.7052,
        "stations": {
            "인천 ○○ 측정소": (37.4563, 126.7052),
            "인천 남동 측정소": (37.4475, 126.7314)
        }
    },
    "수원": {
        "lat": 37.2636,
        "lon": 127.0286,
        "stations": {
            "수원 ○○ 측정소": (37.2636, 127.0286),
            "수원 영통 측정소": (37.2596, 127.0466)
        }
    }
}


# -----------------------------
# 풍향 표시
# -----------------------------

def wind_direction_text(degree):

    directions = [
        "북풍", "북북동풍", "북동풍", "동북동풍",
        "동풍", "동남동풍", "남동풍", "남남동풍",
        "남풍", "남남서풍", "남서풍", "서남서풍",
        "서풍", "서북서풍", "북서풍", "북북서풍"
    ]

    index = int((degree + 11.25) / 22.5) % 16
    return directions[index]


# -----------------------------
# 실제 기상 데이터
# Open-Meteo
# -----------------------------

def get_weather(lat, lon, selected_date, selected_hour):

    today = date.today()

    # 최근 날짜는 forecast API 사용
    if selected_date >= today - timedelta(days=7):

        url = "https://api.open-meteo.com/v1/forecast"

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

    # 과거 날짜는 archive API 사용
    else:

        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": selected_date.strftime("%Y-%m-%d"),
            "end_date": selected_date.strftime("%Y-%m-%d"),
            "hourly": (
                "temperature_2m,"
                "wind_speed_10m,"
                "wind_direction_10m,"
                "surface_pressure"
            ),
            "timezone": "Asia/Seoul"
        }

    try:

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        hourly = data["hourly"]

        target_time = f"{selected_date.strftime('%Y-%m-%d')}T{selected_hour:02d}:00"

        times = hourly["time"]

        if target_time not in times:
            return None

        i = times.index(target_time)

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


# -----------------------------
# 역추적 계산
# -----------------------------

def calculate_backward_path(lat, lon, wind_direction, wind_speed, hours=5):

    points = []

    # 바람이 불어오는 방향을 기준으로
    # 발생원은 바람이 온 방향에 존재한다고 가정

    # 1시간 이동거리(km)
    distance_per_hour = wind_speed * 3.6

    # 역추적이므로 풍향 방향으로 이동
    bearing = math.radians(wind_direction)

    current_lat = lat
    current_lon = lon

    points.append({
        "lat": current_lat,
        "lon": current_lon
    })

    for h in range(1, hours + 1):

        distance = distance_per_hour * h

        # 위도 1도 ≈ 111km
        delta_lat = (
            distance * math.cos(bearing)
        ) / 111

        # 경도 1도 ≈ 111 × cos(latitude)
        delta_lon = (
            distance * math.sin(bearing)
        ) / (111 * math.cos(math.radians(lat)))

        points.append({
            "lat": current_lat + delta_lat,
            "lon": current_lon + delta_lon
        })

    return pd.DataFrame(points)


# -----------------------------
# 발생원 후보
# -----------------------------

def generate_sources(lat, lon, wind_direction):

    # 교육용 발생원 후보
    # 실제 서비스에서는 환경시설 / 도로 / 산업시설 GIS 데이터로 교체

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

        # 측정소에서 발생원으로 향하는 방향
        dy = source["lat"] - lat
        dx = (
            source["lon"] - lon
        ) * math.cos(math.radians(lat))

        angle = math.degrees(math.atan2(dx, dy))

        if angle < 0:
            angle += 360

        # 풍향과 발생원 방향의 차이
        diff = abs(angle - wind_direction)

        if diff > 180:
            diff = 360 - diff

        # 풍향과 가까울수록 높은 점수
        score = max(0, 100 - diff * 1.4)

        source["score"] = round(score)

    return sorted(
        candidates,
        key=lambda x: x["score"],
        reverse=True
    )


# -----------------------------
# 화면
# -----------------------------

st.sidebar.markdown("## ANALYSIS SETTINGS")

region = st.sidebar.selectbox(
    "분석 지역",
    list(LOCATIONS.keys())
)

location_data = LOCATIONS[region]

station_name = st.sidebar.selectbox(
    "측정소",
    list(location_data["stations"].keys())
)

station_lat, station_lon = location_data["stations"][station_name]

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
    min_value=5,
    max_value=50,
    value=15,
    step=5
)

start_button = st.sidebar.button(
    "🔍 발생원 추적 시작",
    use_container_width=True
)

st.markdown(
    '<div class="main-title">PM TRACKER</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">미세먼지 발생원 역추적 시스템</div>',
    unsafe_allow_html=True
)


# -----------------------------
# 초기 화면
# -----------------------------

if not start_button:

    st.markdown(
        '<div class="section-title">SYSTEM READY</div>',
        unsafe_allow_html=True
    )

    st.info(
        "왼쪽의 분석 조건을 설정한 뒤 "
        "'발생원 추적 시작' 버튼을 눌러주세요."
    )

    st.markdown("## 🌫️ 미세먼지는 어디에서 왔을까?")

    st.write(
        "PM TRACKER는 대기질 데이터와 기상 데이터를 결합하여 "
        "미세먼지가 이동해 온 방향을 역추적하는 교육용 분석 시스템입니다."
    )

    st.markdown("### 분석 과정")

    st.write(
        "대기질 데이터 → 풍향·풍속 분석 → "
        "역추적 경로 계산 → 주변 발생원 탐색 → "
        "발생원 가능성 산출"
    )

    st.caption(
        "※ 발생원 분석은 교육용 모델이며 실제 환경정책 판단을 위한 "
        "전문 분석 결과가 아닙니다."
    )

    st.stop()


# -----------------------------
# 실제 기상 데이터 가져오기
# -----------------------------

with st.spinner("실제 기상 데이터를 불러오는 중..."):

    weather = get_weather(
        station_lat,
        station_lon,
        selected_date,
        selected_hour
    )


if weather is None or "error" in weather:

    st.error(
        "기상 데이터를 가져오지 못했습니다. "
        "날짜를 다른 날짜로 선택해 다시 시도해주세요."
    )

    st.stop()


temperature = weather["temperature"]
wind_speed = weather["wind_speed"]
wind_direction = weather["wind_direction"]
pressure = weather["pressure"]

direction_text = wind_direction_text(wind_direction)

estimated_distance = wind_speed * 3.6


# -----------------------------
# 분석 결과
# -----------------------------

st.markdown(
    '<div class="section-title">ATMOSPHERIC ANALYSIS</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "기온",
        f"{temperature:.1f} °C"
    )

with col2:
    st.metric(
        "풍향",
        direction_text
    )

with col3:
    st.metric(
        "풍속",
        f"{wind_speed:.1f} m/s"
    )

with col4:
    st.metric(
        "1시간 예상 이동거리",
        f"{estimated_distance:.1f} km"
    )


st.markdown("---")


# -----------------------------
# 역추적 경로
# -----------------------------

st.markdown(
    '<div class="section-title">BACKWARD TRAJECTORY</div>',
    unsafe_allow_html=True
)

trajectory = calculate_backward_path(
    station_lat,
    station_lon,
    wind_direction,
    wind_speed,
    hours=5
)

# 추적 범위에 맞게 표시
trajectory["lat"] = trajectory["lat"].clip(
    station_lat - tracking_range / 100,
    station_lat + tracking_range / 100
)

trajectory["lon"] = trajectory["lon"].clip(
    station_lon - tracking_range / 100,
    station_lon + tracking_range / 100
)

# 측정소
station_df = pd.DataFrame([
    {
        "lat": station_lat,
        "lon": station_lon
    }
])

# 지도
st.map(
    trajectory,
    latitude="lat",
    longitude="lon",
    zoom=10
)

st.caption(
    f"측정소: {station_name} | "
    f"분석 시각: {selected_date} {selected_hour:02d}:00 | "
    f"풍향: {direction_text}"
)


# -----------------------------
# 발생원 후보
# -----------------------------

st.markdown(
    '<div class="section-title">SOURCE PROBABILITY</div>',
    unsafe_allow_html=True
)

sources = generate_sources(
    station_lat,
    station_lon,
    wind_direction
)

for i, source in enumerate(sources, start=1):

    st.markdown(
        f"""
        <div class="result-box">
            <div class="source-name">
                {i}. {source["name"]}
            </div>

            <div style="color:#8fa1b8;">
                {source["type"]}
            </div>

            <div class="source-score">
                {source["score"]}점
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("---")

st.markdown(
    f"""
    **현재 분석 조건**

    - 지역: {region}
    - 측정소: {station_name}
    - 날짜: {selected_date}
    - 시간: {selected_hour:02d}:00
    - 풍향: {wind_direction:.0f}° ({direction_text})
    - 풍속: {wind_speed:.1f} m/s
    - 기압: {pressure:.0f} hPa
    """,
)

st.caption(
    "※ 현재 버전은 실제 기상 데이터를 이용한 교육용 역추적 시뮬레이션입니다. "
    "발생원 후보는 예시 데이터입니다."
)
