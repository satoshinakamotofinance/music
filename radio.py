import random
import requests
import streamlit as st
from streamlit_extras.switch_page_button import switch_page  # Optional for multi-page
import time

# Custom CSS for modern radio UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .now-playing {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .station-card {
        background: rgba(255,255,255,0.95);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    .favorite-btn {
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        border: none;
        border-radius: 50px;
        padding: 0.8rem 1.5rem;
        font-weight: bold;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    .favorite-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(255,215,0,0.4);
    }
    .surprise-btn {
        background: linear-gradient(45deg, #ff9a9e, #fecfef);
        border-radius: 50px;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-container {
        background: rgba(0,0,0,0.1);
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="🌐 World Radio Hub",
    layout="wide",
    page_icon="🎵",
    initial_sidebar_state="expanded"
)

# Footer goes here (after config)
st.markdown("""
    <div style='text-align: center; padding: 1rem; font-size: 1.1rem; 
         color: #e0e0e0; background: rgba(15,15,35,0.8); 
         border-radius: 15px; margin-top: 2rem;'>
        Developed with ❤️ for the music community by <strong>CA. Ankit Kotriwala</strong>
    </div>
""", unsafe_allow_html=True)


st.markdown("""
<style>
[theme]
primaryColor="#667eea"
backgroundColor="#0f0f23"
secondaryBackgroundColor="#1a1a2e"
textColor="#e0e0e0"
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🌐 World Radio Hub</h1>', unsafe_allow_html=True)

API_BASE = "https://de1.api.radio-browser.info/json"

# ---------- Enhanced caching with better error handling ----------
@st.cache_data(ttl=1800, show_spinner=False)
def get_top_stations(limit=300):
    try:
        url = f"{API_BASE}/stations/topclick"
        resp = requests.get(url, params={"limit": limit, "hidebroken": True}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except:
        return []

@st.cache_data(ttl=3600)
def get_countries():
    try:
        url = f"{API_BASE}/countries"
        resp = requests.get(url, timeout=10)
        return resp.json()
    except:
        return []

@st.cache_data(ttl=3600)
def get_languages():
    try:
        url = f"{API_BASE}/languages"
        resp = requests.get(url, timeout=10)
        return resp.json()
    except:
        return []

@st.cache_data(ttl=3600)
def search_stations_advanced(filters, limit=200):
    url = f"{API_BASE}/stations/search"
    params = {
        "limit": limit,
        "hidebroken": True,
        "has_geo": True,
    }
    for key, value in filters.items():
        if value:
            params[key] = value
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except:
        return []

def enhanced_station_display(s):
    name = s.get("name", "Unknown")[:50]
    country = s.get("country", "🌍")
    bitrate = s.get("bitrate", 0)
    codec = s.get("codec", "?")
    quality = "🔴" if bitrate < 64 else "🟡" if bitrate < 128 else "🟢"
    return f"{name} {quality} [{country}]"

def create_station_card(station, is_playing=False):
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        st.markdown(f"**{station.get('name', 'Unknown')}**")
        st.caption(f"🇸🇽 {station.get('country', 'N/A')} | {station.get('language', 'N/A')}")

    with col2:
        bitrate = station.get("bitrate", 0)
        quality = "🔴 Poor" if bitrate < 64 else "🟡 Good" if bitrate < 128 else "🟢 HQ"
        st.metric("Quality", f"{bitrate}kbps", quality)
        tags = station.get("tags", "")
        if tags:
            st.caption(f"🎯 {tags}")

    with col3:
        favicon = station.get("favicon")
        if favicon:
            st.image(favicon, width=50, use_column_width=None)

# ---------- Global session state ----------
if "current_station" not in st.session_state:
    st.session_state.current_station = None
if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "history" not in st.session_state:
    st.session_state.history = []
if "player_state" not in st.session_state:
    st.session_state.player_state = "stopped"

# ---------- Main layout ----------
header_col1, header_col2 = st.columns([4, 1])

with header_col2:
    if st.button("🎲 Surprise Me!", key="global_surprise", help="Random station from top 200"):
        top_stations = get_top_stations()
        if top_stations:
            st.session_state.current_station = random.choice(top_stations)
            st.session_state.player_state = "playing"
            st.rerun()

# Now playing section (sticky)
if st.session_state.current_station:
    with st.container():
        st.markdown('<div class="now-playing">', unsafe_allow_html=True)
        st.markdown("### 🎵 Now Playing")
        create_station_card(st.session_state.current_station)

        col_btn1, col_audio, col_btn2 = st.columns([1, 4, 1])

        with col_btn1:
            if st.button("★" if st.session_state.current_station.get("stationuuid") not in st.session_state.favorites else "⭐",
                         key="toggle_fav_global", help="Add to favorites"):
                uuid = st.session_state.current_station.get("stationuuid")
                if uuid:
                    if uuid in st.session_state.favorites:
                        st.session_state.favorites.discard(uuid)
                    else:
                        st.session_state.favorites.add(uuid)
                    st.rerun()

        with col_audio:
            stream_url = st.session_state.current_station.get("url_resolved") or st.session_state.current_station.get("url")
            if stream_url:
                st.audio(stream_url, autoplay=True, sample_rate=44100)
            else:
                st.error("❌ No stream available")

        with col_btn2:
            if st.button("⏹️ Stop", key="stop_global"):
                st.session_state.current_station = None
                st.session_state.player_state = "stopped"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("👆 Select a station from tabs below to start listening!")

# ---------- Enhanced sidebar ----------
with st.sidebar:
    st.markdown("### 🎛️ Quick Controls")

    # Load filter data
    countries = get_countries()
    languages = get_languages()

    st.markdown("#### 🌍 Filters")
    country = st.selectbox("Country", [""] + [c["name"] for c in countries[:250]])
    language = st.selectbox("Language", [""] + [l["name"] for l in languages[:250]])
    min_bitrate = st.slider("Min Quality", 0, 320, 64)

    st.markdown("---")

    st.markdown("#### ⭐ Favorites")
    if st.session_state.favorites:
        st.success(f"{len(st.session_state.favorites)} saved")
    else:
        st.info("No favorites yet")

    if st.button("🗑️ Clear All", key="clear_all"):
        st.session_state.favorites.clear()
        st.session_state.history.clear()
        st.session_state.current_station = None
        st.rerun()

# ---------- Main tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Top Hits", "🔍 Discover", "⭐ Favorites", "📜 History"])

with tab1:
    st.header("🌟 Top 300 Global Stations")
    stations = [s for s in get_top_stations(300) if (s.get("bitrate", 0) >= min_bitrate)]

    if stations:
        labels = [enhanced_station_display(s) for s in stations]
        selected = st.selectbox("Pick your station:", labels, key="top_select")
        station = stations[labels.index(selected)]

        if st.button("▶️ Play", key="play_top"):
            st.session_state.current_station = station
            if station.get("stationuuid") not in st.session_state.history:
                st.session_state.history.append(station)
                if len(st.session_state.history) > 20:
                    st.session_state.history.pop(0)
            st.rerun()

with tab2:
    st.header("🧭 Discover New Stations")
    filters = {"country": country, "language": language}
    stations = [s for s in search_stations_advanced(filters, 200) if (s.get("bitrate", 0) >= min_bitrate)]

    if stations:
        labels = [enhanced_station_display(s) for s in stations]
        selected = st.selectbox("Found stations:", labels, key="disc_select")
        station = stations[labels.index(selected)]

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"[🌐 {station.get('homepage', '#')}]({station.get('homepage', '#')})")
        with col2:
            if st.button("▶️ Play", key="play_disc"):
                st.session_state.current_station = station
                st.session_state.history.append(station)
                st.rerun()

with tab3:
    st.header("⭐ Your Favorites")
    fav_stations = []
    all_stations = get_top_stations(500) + search_stations_advanced({}, 500)

    for uuid in st.session_state.favorites:
        for s in all_stations:
            if s.get("stationuuid") == uuid:
                fav_stations.append(s)
                break

    if fav_stations:
        labels = [enhanced_station_display(s) for s in fav_stations]
        selected = st.selectbox("Play favorite:", labels, key="fav_select")
        station = fav_stations[labels.index(selected)]

        if st.button("▶️ Play", key="play_fav"):
            st.session_state.current_station = station
            st.rerun()

with tab4:
    st.header("📜 Recently Played")
    recent = st.session_state.history[-10:][::-1]
    for i, station in enumerate(recent, 1):
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{i}.** {enhanced_station_display(station)}")
            with col2:
                if st.button("▶️", key=f"play_hist_{i}"):
                    st.session_state.current_station = station
                    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Built for music lovers worldwide. Data from [Radio Browser API](https://www.radio-browser.info/)* 🎵✨")
