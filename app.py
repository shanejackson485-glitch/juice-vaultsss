import streamlit as st
import aiohttp
import asyncio

st.set_page_config(page_title="Juice WRLD Vault", page_icon="🕊️", layout="wide")
st.title("🕊️ Juice WRLD Vault")
st.markdown("Search the vault and listen to leaks instantly.")

query = st.text_input("Search for a song...", placeholder="e.g. Lucid Dreams, Goodbye")

if query:
    st.write(f"Searching for **{query}**...")
    
    async def fetch_songs():
        async with aiohttp.ClientSession() as session:
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