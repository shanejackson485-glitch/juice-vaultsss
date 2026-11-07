import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import uvicorn

app = FastAPI(title="Juice WRLD Custom API")

# Allow your website and bot to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SOURCE_API = "https://juicewrldapi.com/juicewrld"

@app.get("/")
async def root():
    return {"status": "online", "message": "Juice WRLD API is running"}

@app.get("/search")
async def search_songs(q: str, limit: int = 10):
    """Search for songs and return clean JSON."""
    async with aiohttp.ClientSession() as session:
        # Fetch from the public source
        async with session.get(f"{SOURCE_API}/songs/", params={"search": q}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Source API failed")
            
            data = await resp.json()
            results = data.get("results", [])[:limit]
            
            clean_results = []
            for song in results:
                path = song.get("path", "")
                clean_results.append({
                    "id": song.get("id"),
                    "title": song.get("name"),
                    "era": song.get("era", {}).get("name"),
                    "length": song.get("length"),
                    "cover": f"https://juicewrldapi.com{song.get('image_url')}" if song.get("image_url") else None,
                    "stream_url": f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}",
                    "download_url": f"https://juicewrldapi.com/juicewrld/files/download/?path={path}"
                })
                
            return {"query": q, "count": len(clean_results), "songs": clean_results}

@app.get("/latest")
async def latest_songs(limit: int = 30):
    """Get the latest leaked songs for the timeline."""
    async with aiohttp.ClientSession() as session:
        # Fetch from the public source, sorted by date
        async with session.get(f"{SOURCE_API}/songs/", params={"sort": "date_leaked", "order": "desc", "limit": limit}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Source API failed")
            
            data = await resp.json()
            results = data.get("results", [])
            
            clean_results = []
            for song in results:
                path = song.get("path", "")
                clean_results.append({
                    "id": song.get("id"),
                    "title": song.get("name"),
                    "era": song.get("era", {}).get("name"),
                    "length": song.get("length"),
                    "cover": f"https://juicewrldapi.com{song.get('image_url')}" if song.get("image_url") else None,
                    "stream_url": f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}",
                    "download_url": f"https://juicewrldapi.com/juicewrld/files/download/?path={path}"
                })
                
            return {"count": len(clean_results), "songs": clean_results}

if __name__ == "__main__":
    # Pterodactyl usually sets SERVER_PORT in the environment. 
    # If not, it defaults to 8000.
    port = int(os.environ.get("SERVER_PORT", 8000))
    
    print(f"Starting API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)