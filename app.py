import streamlit as st
import aiohttp
import asyncio
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="Juice WRLD Vault", page_icon="🕊️", layout="wide")

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f1115 0%, #181a20 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        color: #b9bbbe;
        background-color: transparent;
        border: none;
        padding: 10px 0px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 3px solid #b90000 !important;
    }

    /* Search Bar */
    .stTextInput > div > div > input {
        background-color: #202225;
        color: white;
        border: 1px solid #40444b;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 16px;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border: 1px solid #b90000;
        box-shadow: 0 0 0 2px rgba(185, 0, 0, 0.2);
    }

    /* Song Cards */
    div.css-1r6slb0, div.css-12oz5g7 {
        background-color: #202225;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2f3136;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 20px;
    }
    div.css-1r6slb0:hover, div.css-12oz5g7:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.6);
        border: 1px solid #b90000;
    }

    /* Discord Button */
    .discord-btn {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #5865F2;
        color: white !important;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        font-size: 15px;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: background-color 0.2s, transform 0.2s;
        z-index: 9999;
    }
    .discord-btn:hover {
        background-color: #4752C4;
        transform: scale(1.05);
        color: white !important;
    }

    /* Hide Streamlit default menu/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- DISCORD BUTTON ---
# REPLACE THIS URL WITH YOUR ACTUAL DISCORD INVITE LINK
st.markdown('<a href="https://discord.gg/YOUR_INVITE_LINK" target="_blank" class="discord-btn">Join our Discord</a>', unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🕊️ Juice WRLD Vault</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #b9bbbe; font-size: 18px;'>Search the vault and listen to leaks instantly.</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

API_URL = "https://juicewrldapi.com"

async def fetch_api(endpoint: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{endpoint}") as resp:
            if resp.status == 200:
                return await resp.json()
            return None

def render_song_card(song):
    with st.container():
        img_url = song.get("image_url") or song.get("cover")
        if img_url:
            if img_url.startswith("/"):
                img_url = f"https://juicewrldapi.com{img_url}"
            st.image(img_url, use_column_width=True)
        else:
            st.image("https://juicewrldapi.com/juicewrld/cover/default.png", use_column_width=True)

        st.markdown(f"### {song.get('name', song.get('title', 'Unknown'))}")
        
        era = song.get('era', {}).get('name', 'Unknown Era')
        length = song.get('length', '')
        st.markdown(f"<span style='color: #b9bbbe; font-size: 14px;'>**Era:** {era} &nbsp;|&nbsp; **Length:** {length}</span>", unsafe_allow_html=True)
        
        path = song.get("path", "")
        if path:
            stream_url = f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}"
            st.audio(stream_url)

# --- TABS ---
tab_search, tab_timeline = st.tabs(["Search Vault", "Latest Surfaces (Timeline)"])

# --- SEARCH TAB ---
with tab_search:
    query = st.text_input("", placeholder="Search for a song (e.g. Lucid Dreams, Goodbye)...", label_visibility="collapsed")
    if query:
        with st.spinner("Searching the vault..."):
            async def fetch_songs():
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{API_URL}/juicewrld/songs/?search={urllib.parse.quote(query)}") as resp:
                        if resp.status != 200: return []
                        data = await resp.json()
                        return data.get("results", [])
                        
            results = asyncio.run(fetch_songs())
            
            if not results:
                st.error("No songs found.")
            else:
                cols = st.columns(3)
                for idx, song in enumerate(results[:12]):
                    with cols[idx % 3]:
                        render_song_card(song)

# --- TIMELINE TAB ---
with tab_timeline:
    st.markdown("### Recent Surfaces")
    st.markdown("The latest leaked Juice WRLD tracks, updated automatically.")
    
    with st.spinner("Loading latest leaks..."):
        async def fetch_latest():
            async with aiohttp.ClientSession() as session:
                # Fetching a larger batch to filter by newest
                async with session.get(f"{API_URL}/juicewrld/songs/?sort=date_leaked&order=desc&limit=30") as resp:
                    if resp.status != 200: return []
                    data = await resp.json()
                    return data.get("results", [])
                    
        latest_songs = asyncio.run(fetch_latest())
        
        if not latest_songs:
            st.info("No recent leaks found.")
        else:
            # Render them in a 2-column layout for a timeline feed look
            cols = st.columns(2)
            for idx, song in enumerate(latest_songs):
                with cols[idx % 2]:
                    render_song_card(song)