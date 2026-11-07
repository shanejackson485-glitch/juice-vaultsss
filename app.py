import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="Juice WRLD Vault", page_icon="🕊️", layout="wide")

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f1115 0%, #181a20 100%); color: #e0e0e0; }
    h1, h2, h3 { color: #ffffff !important; }
    .stTextInput > div > div > input {
        background-color: #202225; color: white; border: 1px solid #40444b;
        border-radius: 8px; padding: 14px; font-size: 16px;
    }
    div.css-1r6slb0, div.css-12oz5g7 {
        background-color: #202225; border-radius: 12px; padding: 20px;
        border: 1px solid #2f3136; transition: transform 0.2s;
    }
    div.css-1r6slb0:hover { transform: translateY(-5px); border: 1px solid #b90000; }
    .discord-btn {
        position: fixed; top: 20px; right: 20px; background-color: #5865F2;
        color: white !important; padding: 10px 24px; border-radius: 8px;
        font-weight: 600; text-decoration: none; z-index: 9999;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown('<a href="https://discord.gg/YOUR_INVITE_LINK" target="_blank" class="discord-btn">Join our Discord</a>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>🕊️ Juice WRLD Vault</h1>", unsafe_allow_html=True)

API_URL = "https://juicewrldapi.com"

# We use st.cache_data so it doesn't re-fetch the same data 100 times
@st.cache_data(ttl=300)
def fetch_songs(query: str):
    try:
        res = requests.get(f"{API_URL}/juicewrld/songs/", params={"search": query})
        if res.status_code == 200:
            return res.json().get("results", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=300)
def fetch_latest():
    try:
        res = requests.get(f"{API_URL}/juicewrld/songs/", params={"sort": "date_leaked", "order": "desc", "limit": 30})
        if res.status_code == 200:
            return res.json().get("results", [])
    except Exception:
        pass
    return []

def render_song_card(song):
    with st.container():
        img_url = song.get("image_url")
        if img_url:
            if img_url.startswith("/"): img_url = f"https://juicewrldapi.com{img_url}"
            st.image(img_url, use_column_width=True)
        
        st.markdown(f"### {song.get('name', 'Unknown')}")
        st.caption(f"Era: {song.get('era', {}).get('name', 'Unknown')} | {song.get('length', '')}")
        
        path = song.get("path", "")
        if path:
            stream_url = f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}"
            st.audio(stream_url)

tab_search, tab_timeline = st.tabs(["Search Vault", "Latest Surfaces"])

with tab_search:
    query = st.text_input("", placeholder="Search...", label_visibility="collapsed")
    if query:
        with st.spinner("Searching..."):
            results = fetch_songs(query)
            if results:
                cols = st.columns(3)
                for idx, song in enumerate(results[:12]):
                    with cols[idx % 3]: render_song_card(song)
            else: st.error("No songs found.")

with tab_timeline:
    with st.spinner("Loading timeline..."):
        latest = fetch_latest()
        if latest:
            cols = st.columns(2)
            for idx, song in enumerate(latest):
                with cols[idx % 2]: render_song_card(song)
        else: st.error("Failed to load timeline.")