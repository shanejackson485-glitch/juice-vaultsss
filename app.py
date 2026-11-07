import streamlit as st
import requests

st.set_page_config(page_title="Juice WRLD API", page_icon="🕊️", layout="wide", initial_sidebar_state="expanded")

# --- MASSIVE CUSTOM CSS UPGRADE ---
st.markdown("""
<style>
    /* Global Theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #0d0f12;
        color: #e0e0e0;
    }
    
    /* Hide Streamlit Headers */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Top Navigation Bar */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1a1d24;
        padding: 15px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #2a2e39;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .top-bar-title {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .top-bar-title h1 {
        color: white;
        font-size: 24px;
        margin: 0;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .top-bar-stats {
        display: flex;
        gap: 20px;
        color: #9ca3af;
        font-size: 14px;
        font-weight: 600;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #12141a;
        border-right: 1px solid #2a2e39;
    }
    [data-testid="stSidebar"] h2 {
        color: white;
        font-size: 16px;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Inputs & Selects */
    div[data-baseweb="select"] > div, .stTextInput > div > div > input {
        background-color: #1a1d24 !important;
        border: 1px solid #3b404d !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Grid Layout for Songs */
    .song-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 20px;
    }
    
    /* Song Card */
    .song-card {
        background-color: #1a1d24;
        border-radius: 12px;
        border: 1px solid #2a2e39;
        overflow: hidden;
        transition: all 0.3s ease;
        position: relative;
    }
    .song-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
        box-shadow: 0 10px 20px rgba(0,0,0,0.5);
    }
    .song-image {
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
        border-bottom: 1px solid #2a2e39;
    }
    .song-content {
        padding: 15px;
    }
    .song-title {
        color: white;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .song-meta {
        color: #9ca3af;
        font-size: 13px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    /* Category Badge */
    .badge {
        position: absolute;
        top: 10px;
        right: 10px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        color: black;
        text-transform: uppercase;
    }
    .badge-unreleased { background-color: #f59e0b; }
    .badge-released { background-color: #10b981; }
    .badge-unsurfaced { background-color: #3b82f6; color: white;}
    .badge-session { background-color: #8b5cf6; color: white;}
    
    /* Audio Player Overwrite */
    audio {
        width: 100%;
        margin-top: 10px;
        height: 35px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "https://juicewrldapi.com"

@st.cache_data(ttl=300)
def fetch_songs(query="", category="", era="", limit=24):
    params = {"limit": limit, "sort": "date_leaked", "order": "desc"}
    if query: params["search"] = query
    if category and category != "All": params["category"] = category
    if era and era != "All": params["era"] = era
    
    try:
        res = requests.get(f"{API_URL}/juicewrld/songs/", params=params)
        if res.status_code == 200:
            return res.json().get("results", [])
    except Exception:
        pass
    return []

# --- SIDEBAR (Filters) ---
with st.sidebar:
    st.image("https://juicewrldapi.com/logo.png", width=80)
    st.markdown("## Filters")
    
    query = st.text_input("Search Vault", placeholder="e.g. Lucid Dreams")
    st.markdown("---")
    
    category = st.selectbox("Category", ["All", "Unreleased", "Released", "Recording Session", "Unsurfaced"])
    era = st.selectbox("Era", ["All", "jute", "GB&GR", "DRFL", "LND", "FD", "TPNE"])
    
    st.markdown("---")
    if st.button("Refresh Database", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- MAIN PAGE ---
# Top Bar
st.markdown("""
<div class="top-bar">
    <div class="top-bar-title">
        <h1>The Juice WRLD API</h1>
    </div>
    <div class="top-bar-stats">
        <span>SONGS: 2,774</span>
        <span>ALBUMS: 24</span>
        <span>ERAS: 34</span>
        <span>SERVER: 🟢</span>
    </div>
</div>
""", unsafe_allow_html=True)

songs = fetch_songs(query, category, era)

if not songs:
    st.error("No songs found. Try adjusting your filters.")
else:
    # We have to build the grid manually using columns to embed Streamlit audio players
    num_cols = 3
    cols = st.columns(num_cols)
    
    for idx, song in enumerate(songs):
        with cols[idx % num_cols]:
            img = song.get("image_url", "")
            img_url = f"https://juicewrldapi.com{img}" if img.startswith("/") else "https://juicewrldapi.com/default.png"
            
            title = song.get("name", "Unknown")
            s_era = song.get("era", {}).get("name", "Unknown").upper()
            length = song.get("length", "")
            leak_type = song.get("leak_type", "Unknown").lower()
            path = song.get("path", "")
            
            # Determine Badge Style
            badge_class = "badge"
            if "unreleased" in leak_type: badge_class += " badge-unreleased"
            elif "released" in leak_type: badge_class += " badge-released"
            elif "unsurfaced" in leak_type: badge_class += " badge-unsurfaced"
            elif "session" in leak_type: badge_class += " badge-session"
            
            # Display Card HTML
            html_card = f"""
            <div class="song-card">
                <div style="position: relative;">
                    <span class="{badge_class}">{leak_type}</span>
                    <img src="{img_url}" class="song-image">
                </div>
                <div class="song-content">
                    <div class="song-title" title="{title}">{title}</div>
                    <div class="song-meta">🕒 Era: <span style="color: #3b82f6; font-weight: 600;">{s_era}</span></div>
                    <div class="song-meta">⏱️ Length: {length}</div>
                </div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)
            
            # Native Streamlit audio player placed right below the card
            if path:
                stream_url = f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}"
                st.audio(stream_url, format="audio/mp3")
            else:
                st.caption("Audio unavailable.")
                
            st.markdown("<br>", unsafe_allow_html=True)