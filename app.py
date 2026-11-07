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
    st.markdown('<a href="https://discord.gg/grails" target="_blank" class="discord-btn">Join our Discord</a>', unsafe_allow_html=True)

query = st.text_input("Search for a song...", placeholder="e.g. Lucid Dreams, Goodbye")

if query:
    with st.spinner("Searching..."):
        async def fetch_songs():
            async with aiohttp.ClientSession() as session:
                # Pointing directly to the public API, not localhost
                async with session.get(f"https://juicewrldapi.com/juicewrld/songs/?search={query}") as resp:
                    data = await resp.json()
                    return data.get("results", [])
                    
        results = asyncio.run(fetch_songs())
        
        if not results:
            st.error("No songs found.")
        else:
            cols = st.columns(3)
            for idx, song in enumerate(results[:15]):
                with cols[idx % 3]:
                    img_url = song.get("image_url")
                    if img_url:
                        st.image(f"https://juicewrldapi.com{img_url}", use_column_width=True)
                    
                    st.subheader(song.get("name", "Unknown"))
                    st.caption(f"Era: {song.get('era', {}).get('name', 'Unknown')}")
                    
                    path = song.get("path", "")
                    if path:
                        stream_url = f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}"
                        st.audio(stream_url)