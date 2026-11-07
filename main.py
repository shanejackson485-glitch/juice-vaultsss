from __future__ import annotations
import os
from typing import Any
from urllib.parse import urlencode
import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
CATALOGUE = os.getenv('JUICEWRLD_IO_API', 'https://juicewrld.io/api/v1').rstrip('/')
MEDIA = os.getenv('JUICEWRLD_API', 'https://juicewrldapi.com').rstrip('/')
API_KEY = os.getenv('VAULT_API_KEY', '').strip()
app = FastAPI(title='Juice WRLD Vault API', version='2.0.0', description='Bot-friendly JSON API for the Juice WRLD Vault.')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['GET','HEAD','OPTIONS'], allow_headers=['*'])

async def auth(x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, 'Invalid or missing X-API-Key')

async def upstream(url: str, params: dict[str, Any] | None = None):
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(url, params=params)
        if r.status_code == 429:
            raise HTTPException(429, 'Upstream rate limit reached', headers={'Retry-After': r.headers.get('Retry-After','30')})
        if r.status_code == 404:
            raise HTTPException(404, 'Not found')
        r.raise_for_status()
        return r.json()
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(502, 'Upstream API unavailable')

@app.get('/')
async def root():
    return {'name':'Juice WRLD Vault API','version':'2.0.0','status':'online','docs':'/docs','base':'/api/v1'}

@app.get('/health')
async def health():
    return {'status':'ok','service':'Juice WRLD Vault API'}

@app.get('/api/v1/songs', dependencies=[Depends(auth)])
async def songs(q: str | None=None, status: str | None=None, era: str | None=None, project: str | None=None, person: str | None=None, family: str | None=None, hasAudio: bool | None=None, hasLyrics: bool | None=None, limit: int=Query(50,ge=1,le=200), offset: int=Query(0,ge=0)):
    params={k:v for k,v in locals().items() if v is not None}
    return await upstream(f'{CATALOGUE}/songs', params)

@app.get('/api/v1/songs/{song_id}', dependencies=[Depends(auth)])
async def song(song_id: str): return await upstream(f'{CATALOGUE}/songs/{song_id}')
@app.get('/api/v1/eras', dependencies=[Depends(auth)])
async def eras(): return await upstream(f'{CATALOGUE}/eras')
@app.get('/api/v1/eras/{code}', dependencies=[Depends(auth)])
async def era(code: str): return await upstream(f'{CATALOGUE}/eras/{code}')
@app.get('/api/v1/projects', dependencies=[Depends(auth)])
async def projects(): return await upstream(f'{CATALOGUE}/projects')
@app.get('/api/v1/projects/{slug}', dependencies=[Depends(auth)])
async def project(slug: str): return await upstream(f'{CATALOGUE}/projects/{slug}')
@app.get('/api/v1/people', dependencies=[Depends(auth)])
async def people(): return await upstream(f'{CATALOGUE}/people')
@app.get('/api/v1/people/{slug}', dependencies=[Depends(auth)])
async def person(slug: str): return await upstream(f'{CATALOGUE}/people/{slug}')
@app.get('/api/v1/search', dependencies=[Depends(auth)])
async def search(q: str=Query(min_length=2), limit: int=Query(20,ge=1,le=50)):
    return await upstream(f'{CATALOGUE}/search', {'q':q,'limit':limit})
@app.get('/api/v1/stats', dependencies=[Depends(auth)])
async def stats(): return await upstream(f'{CATALOGUE}/stats')
@app.get('/api/v1/media/search', dependencies=[Depends(auth)])
async def media_search(q: str=Query(min_length=1), limit: int=Query(24,ge=1,le=100)):
    return await upstream(f'{MEDIA}/juicewrld/songs/', {'search':q,'limit':limit})
@app.get('/api/v1/radio/random', dependencies=[Depends(auth)])
async def radio_random(): return await upstream(f'{MEDIA}/juicewrld/radio/random/')
@app.get('/api/v1/media/download', dependencies=[Depends(auth)])
async def media_download(path: str=Query(min_length=1)):
    return {'url':f'{MEDIA}/juicewrld/files/download-compressed/?{urlencode({"path":path})}','source':'juicewrldapi.com'}
