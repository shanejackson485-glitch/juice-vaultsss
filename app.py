import streamlit as st
import requests

st.set_page_config(page_title="Juice WRLD Vault", page_icon="🕊️", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS & FONTS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* Base Styling */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #090a0f 0%, #15171e 100%); color: #e0e0e0; }
    
    /* Hide Streamlit Junk */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 50px; }

    /* Top Nav Bar */
    .nav-bar {
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(26, 29, 36, 0.7); backdrop-filter: blur(10px);
        padding: 15px 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .nav-title { color: white; font-size: 24px; font-weight: 800; margin: 0; display: flex; align-items: center; gap: 10px; }
    
    /* Hero Banner */
    .hero {
        background: linear-gradient(90deg, rgba(59,130,246,0.15) 0%, rgba(0,0,0,0) 100%);
        border: 1px solid rgba(59,130,246,0.3); border-radius: 20px;
        padding: 40px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;
    }
    .hero-title { font-size: 36px; font-weight: 800; color: white; margin: 0; }
    .hero-subtitle { color: #9ca3af; font-size: 16px; margin-top: 5px; }

    /* Song Cards */
    .song-card {
        background: #15171e; border-radius: 16px; border: 1px solid #2a2e39;
        overflow: hidden; transition: all 0.3s ease; position: relative; margin-bottom: 20px;
    }
    .song-card:hover { transform: translateY(-8px); border-color: #3b82f6; box-shadow: 0 15px 30px rgba(59,130,246,0.15); }
    .song-image { width: 100%; aspect-ratio: 1/1; object-fit: cover; transition: 0.3s; }
    .song-card:hover .song-image { transform: scale(1.05); }
    .song-content { padding: 20px; }
    .song-title { color: white; font-size: 20px; font-weight: 800; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .song-meta { color: #9ca3af; font-size: 13px; margin-bottom: 5px; display: flex; align-items: center; gap: 6px; }
    
    /* Badges */
    .badge { position: absolute; top: 15px; right: 15px; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; color: black; text-transform: uppercase; letter-spacing: 0.5px; backdrop-filter: blur(5px); }
    .badge-unreleased { background-color: rgba(245, 158, 11, 0.9); }
    .badge-released { background-color: rgba(16, 185, 129, 0.9); }
    .badge-unsurfaced { background-color: rgba(59, 130, 246, 0.9); color: white;}
    .badge-session { background-color: rgba(139, 92, 246, 0.9); color: white;}

    /* Inputs & Buttons */
    .stTextInput > div > div > input {
        background: rgba(26, 29, 36, 0.8) !important; border: 1px solid #3b404d !important;
        color: white !important; border-radius: 12px !important; padding: 12px 20px !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important; color: white !important;
        border-radius: 12px !important; font-weight: 700 !important; border: none !important;
        width: 100%; padding: 12px !important; transition: 0.2s;
    }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 15px rgba(59,130,246,0.5); }
</style>
""", unsafe_allow_html=True)

# --- API SETUP ---
API_URL = "https://juicewrldapi.com"

@st.cache_data(ttl=300)
def fetch_songs(query=""):
    params = {"limit": 24}
    if query: params["search"] = query
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

# --- TOP NAV ---
st.markdown("""
<div class="nav-bar">
    <div class="nav-title">🕊️ Juice WRLD Vault</div>
    <div style="color: #9ca3af; font-size: 14px; font-weight: 600;">
        SONGS: 3,137 &nbsp; | &nbsp; ERAS: 11 &nbsp; | &nbsp; 🟢 37 Online
    </div>
</div>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
random_song = fetch_random()
if random_song:
    st.markdown(f"""
    <div class="hero">
        <div>
            <div style="color: #3b82f6; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;">Song of the Hour</div>
            <h1 class="hero-title">{random_song.get('name', 'Unknown')}</h1>
            <p class="hero-subtitle">{random_song.get('era', {}).get('name', 'Unknown')} • {random_song.get('length', '')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- SEARCH ---
query = st.text_input("Search the vault...", placeholder="e.g. Lucid Dreams", label_visibility="visible")
if st.button("Search"):
    st.cache_data.clear()

# --- SONG GRID ---
songs = fetch_songs(query)
if not songs:
    st.error("No songs found.")
else:
    cols = st.columns(4)
    for idx, song in enumerate(songs):
        with cols[idx % 4]:
            img = song.get("image_url", "")
            img_url = f"https://juicewrldapi.com{img}" if img.startswith("/") else "https://juicewrldapi.com/default.png"
            title = song.get("name", "Unknown")
            s_era = song.get("era", {}).get("name", "Unknown").upper()
            leak_type = song.get("leak_type", "Unknown").lower()
            
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
                    <div class="song-title">{title}</div>
                    <div class="song-meta">💿 {s_era}</div>
                </div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)