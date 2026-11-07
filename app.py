import streamlit as st
import aiohttp
import asyncio
import urllib.parse
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 1. THE API (Backend)
# ==========================================
api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SOURCE_API = "https://juicewrldapi.com/juicewrld"

@api.get("/api/search")
async def api_search(q: str, limit: int = 10):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/songs/", params={"search": q}) as resp:
            if resp.status != 200: return {"error": "Source API failed"}
            data = await resp.json()
            results = data.get("results", [])[:limit]
            
            clean = []
            for song in results:
                path = song.get("path", "")
                clean.append({
                    "title": song.get("name"),
                    "era": song.get("era", {}).get("name"),
                    "cover": f"https://juicewrldapi.com{song.get('image_url')}" if song.get("image_url") else None,
                    "stream_url": f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}",
                })
            return {"songs": clean}

@api.get("/api/latest")
async def api_latest(limit: int = 30):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/songs/", params={"sort": "date_leaked", "order": "desc", "limit": limit}) as resp:
            if resp.status != 200: return {"error": "Source API failed"}
            data = await resp.json()
            return {"songs": data.get("results", [])}

# Start FastAPI in a background thread so Streamlit can run at the same time
def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)

if "api_started" not in st.session_state:
    st.session_state["api_started"] = True
    threading.Thread(target=run_api, daemon=True).start()

# ==========================================
# 2. THE WEBSITE (Frontend)
# ==========================================

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

API_URL = "http://127.0.0.1:8000" # Points to the API running in the same file

async def fetch_api(endpoint: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{endpoint}") as resp:
            if resp.status == 200:
                return await resp.json()
            return None

def render_song_card(song):
    with st.container():
        img_url = song.get("cover") or song.get("image_url")
        if img_url and img_url.startswith("/"): img_url = f"https://juicewrldapi.com{img_url}"
        if img_url: st.image(img_url, use_column_width=True)
        
        st.markdown(f"### {song.get('title', song.get('name', 'Unknown'))}")
        st.caption(f"Era: {song.get('era', {}).get('name', 'Unknown')} | {song.get('length', '')}")
        
        if song.get("stream_url"):
            st.audio(song["stream_url"])

tab_search, tab_timeline = st.tabs(["Search Vault", "Latest Surfaces"])

with tab_search:
    query = st.text_input("", placeholder="Search...", label_visibility="collapsed")
    if query:
        with st.spinner("Searching..."):
            data = asyncio.run(fetch_api(f"/api/search?q={urllib.parse.quote(query)}"))
            if data and data.get("songs"):
                cols = st.columns(3)
                for idx, song in enumerate(data["songs"][:12]):
                    with cols[idx % 3]: render_song_card(song)
            else: st.error("No songs found.")

with tab_timeline:
    with st.spinner("Loading timeline..."):
        data = asyncio.run(fetch_api("/api/latest"))
        if data and data.get("songs"):
            cols = st.columns(2)
            for idx, song in enumerate(data["songs"]):
                with cols[idx % 2]:
                    # We use the raw format for the timeline
                    with st.container():
                        img_url = song.get("image_url")
                        if img_url: st.image(f"https://juicewrldapi.com{img_url}", use_column_width=True)
                        st.markdown(f"### {song.get('name', 'Unknown')}")
                        st.caption(f"Era: {song.get('era', {}).get('name', 'Unknown')}")
                        if song.get("path"):
                            st.audio(f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={song['path']}")
        else: st.error("Failed to load timeline.")