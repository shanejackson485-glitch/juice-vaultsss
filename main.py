import os
import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# This tells FastAPI where your HTML file is
templates = Jinja2Templates(directory="templates")

SOURCE_API = "https://juicewrldapi.com/juicewrld"

# --- FRONTEND (Serves the website) ---
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- API ENDPOINTS ---
@app.get("/api/latest")
async def latest_songs(limit: int = 20):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/songs/", params={"sort": "date_leaked", "order": "desc", "limit": limit}) as resp:
            if resp.status != 200:
                return {"error": "Failed"}
            data = await resp.json()
            return {"songs": data.get("results", [])}

@app.get("/api/search")
async def search_songs(q: str, limit: int = 20):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/songs/", params={"search": q, "limit": limit}) as resp:
            if resp.status != 200:
                return {"error": "Failed"}
            data = await resp.json()
            return {"songs": data.get("results", [])}

@app.get("/api/random")
async def random_song():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SOURCE_API}/radio/random/") as resp:
            if resp.status != 200:
                return {"error": "Failed"}
            data = await resp.json()
            return data

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)