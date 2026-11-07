from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import uvicorn

app = FastAPI(title="Juice WRLD Custom API")

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
    """Search for songs."""
    async with aiohttp.ClientSession() as session:
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

@app.get("/random")
async def random_song():
    """Get a random playable song."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/radio/random/") as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Source API failed")
            data = await resp.json()
            song = data.get("song", {})
            path = song.get("path", "")
            
            return {
                "title": song.get("name"),
                "era": song.get("era", {}).get("name"),
                "stream_url": f"https://juicewrldapi.com/juicewrld/files/download-compressed/?path={path}",
                "download_url": f"https://juicewrldapi.com/juicewrld/files/download/?path={path}"
            }

@app.get("/category/{category}")
async def get_by_category(category: str, limit: int = 20):
    """Get songs by category (e.g., unreleased, released, unsurfaced)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/songs/", params={"category": category, "limit": limit}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Source API failed")
            data = await resp.json()
            
            results = data.get("results", [])
            return {"category": category, "count": len(results), "songs": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)