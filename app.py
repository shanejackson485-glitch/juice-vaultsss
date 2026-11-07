import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Juice WRLD Vault", page_icon="🕊️", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0d0f12; color: #e0e0e0; }
    
    /* Hide Streamlit Headers */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Top Navigation Bar */
    .top-bar {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1d24; padding: 15px 30px; border-radius: 12px;
        margin-bottom: 25px; border: 1px solid #2a2e39;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .top-bar-title h1 { color: white; font-size: 24px; margin: 0; font-weight: 800; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #12141a; border-right: 1px solid #2a2e39; }
    [data-testid="stSidebar"] h2 { color: white; font-size: 16px; text-transform: uppercase; }
    
    /* Inputs */
    div[data-baseweb="select"] > div, .stTextInput > div > div > input {
        background-color: #1a1d24 !important; border: 1px solid #3b404d !important;
        color: white !important; border-radius: 8px !important;
    }
    
    /* Song Cards */
    .song-card {
        background-color: #1a1d24; border-radius: 12px; border: 1px solid #2a2e39;
        overflow: hidden; transition: all 0.3s ease; position: relative; margin-bottom: 15px;
    }
    .song-card:hover { transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
    .song-image { width: 100%; aspect-ratio: 1/1; object-fit: cover; border-bottom: 1px solid #2a2e39; }
    .song-content { padding: 15px; }
    .song-title { color: white; font-size: 18px; font-weight: 800; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .song-meta { color: #9ca3af; font-size: 13px; margin-bottom: 4px; }
    
    /* Category Badges */
    .badge { position: absolute; top: 10px; right: 10px; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 800; color: black; text-transform: uppercase; }
    .badge-unreleased { background-color: #f59e0b; }
    .badge-released { background-color: #10b981; }
    .badge-unsurfaced { background-color: #3b82f6; color: white;}
    .badge-session { background-color: #8b5cf6; color: white;}
    
    /* Audio Player */
    audio { width: 100%; margin-top: 10px; height: 35px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
# USING THE PUBLIC API SO IT WORKS RIGHT NOW.
# If you get Render working, change this to your Render URL (e.g., "https://juice-api.onrender.com")
API_URL = "https://juicewrldapi.com"

@st.cache_data(ttl=300)
def fetch_songs(query="", category="", limit=24):
    params = {"limit": limit}
    if query: params["search"] = query
    if category and category != "All": params["category"] = category
    
    try:
        res = requests.get(f"{API_URL}/juicewrld/songs/", params=params)
        if res.status_code == 200:
            return res.json().get("results", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=300)
def fetch_random():
    try:
        res = requests.get(f"{API_URL}/juicewrld/radio/random/")
        if res.status_code == 200:
            return res.json().get("song", {})
    except Exception:
        pass
    return {}

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://juicewrldapi.com/logo.png", width=80)
    st.markdown("## Filters")
    query = st.text_input("Search Vault", placeholder="e.g. Lucid Dreams")
    st.markdown("---")
    category = st.selectbox("Category", ["All", "Unreleased", "Released", "Recording Session", "Unsurfaced"])
    st.markdown("---")
    if st.button("Refresh Database", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- TOP BAR ---
st.markdown("""
<div class="top-bar">
    <div class="top-bar-title"><h1>The Juice WRLD API</h1></div>
</div>
""", unsafe_allow_html=True)

# --- MAIN GRID ---
col_left, col_right = st.columns([2, 1])

with col_left:
    songs = fetch_songs(query, category)
    if not songs:
        st.error("No songs found.")
    else:
        cols = st.columns(2)
        for idx, song in enumerate(songs):
            with cols[idx % 2]:
                img = song.get("image_url", "")
                img_url = f"https://juicewrldapi.com{img}" if img.startswith("/") else "https://juicewrldapi.com/default.png"
                title = song.get("name", "Unknown")
                s_era = song.get("era", {}).get("name", "Unknown").upper()
                length = song.get("length", "")
                leak_type = song.get("leak_type", "Unknown").lower()
                path = song.get("path", "")
                
                badge_class = "badge"
                if "unreleased" in leak_type: badge_class += " badge-unreleased"
                elif "released" in leak_type: badge_class += " badge-released"
                elif "unsurfaced" in leak_type: badge_class += " badge-unsurfaced"
                elif "session" in leak_type: badge_class += " badge-session"
                
                html_card = f"""
                <div class="song-card">
                    <div style="position: relative;">
                        <span class="{badge_class}">{leak_type}</span>
                        <img src="{img_url}" class="song-image">
                    </div>
                    <div class="song-content">
                        <div class="song-title" title="{title}">{title}</div>
                        <div class="song-meta">🕒 Era: <span style="color: #3b82f6; font-weight: 600;">{s_era}</span></div>
                        <div class="song-meta">⏱️ {length}</div>
                    </div>
                </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
                
                if path:
                    stream_url = f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}"
                    st.audio(stream_url, format="audio/mp3")
                st.markdown("<br>", unsafe_allow_html=True)

with col_right:
    st.markdown("### Song of the Hour")
    random_song = fetch_random()
    if random_song:
        st.markdown(f"**{random_song.get('name', 'Unknown')}**")
        st.caption(f"{random_song.get('era', {}).get('name', 'Unknown')} • {random_song.get('length', '')}")