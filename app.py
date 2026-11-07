import streamlit as st
import aiohttp
import asyncio

st.set_page_config(page_title="Juice WRLD Vault", page_icon="🕊️", layout="wide")

# --- CUSTOM CSS FOR DISCORD BUTTON ---
st.markdown("""
<style>
    .discord-btn {
        background-color: #5865F2;
        color: white !important;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 8px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .discord-btn:hover {
        background-color: #4752C4;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🕊️ Juice WRLD Vault")
    st.markdown("Search the vault and listen to leaks instantly.")
with col2:
    # REPLACE THIS URL WITH YOUR ACTUAL DISCORD INVITE LINK
    st.markdown('<a href="https://discord.gg/YOUR_INVITE_LINK" target="_blank" class="discord-btn">Join our Discord</a>', unsafe_allow_html=True)

# Tabs
tab1, tab2 = st.tabs(["Search", "Categories"])

# NOTE: Replace `http://localhost:8000` with your actual API URL if hosted elsewhere
API_URL = "http://localhost:8000"

async def fetch_api(endpoint: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{endpoint}") as resp:
            if resp.status == 200:
                return await resp.json()
            return None

def render_song_grid(songs, cols_count=3):
    cols = st.columns(cols_count)
    for idx, song in enumerate(songs):
        with cols[idx % cols_count]:
            if song.get("cover"):
                st.image(song["cover"], use_column_width=True)
            st.subheader(song.get("title", "Unknown"))
            st.caption(f"Era: {song.get('era', 'Unknown')} | {song.get('length', '')}")
            if song.get("stream_url"):
                st.audio(song["stream_url"])

# --- SEARCH TAB ---
with tab1:
    query = st.text_input("Search for a song...", placeholder="e.g. Lucid Dreams, Goodbye")
    if query:
        with st.spinner("Searching..."):
            data = asyncio.run(fetch_api(f"/search?q={query}"))
            if data and data.get("songs"):
                render_song_grid(data["songs"])
            else:
                st.error("No songs found or API is offline.")

# --- CATEGORIES TAB ---
with tab2:
    category = st.selectbox("Select Category", ["unreleased", "released", "unsurfaced", "recording_session"])
    if st.button("Load Category"):
        with st.spinner("Fetching..."):
            data = asyncio.run(fetch_api(f"/category/{category}"))
            if data and data.get("songs"):
                render_song_grid(data["songs"])
            else:
                st.error("No songs found or API is offline.")