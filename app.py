import os, html, requests, streamlit as st
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='Juice WRLD Vault', page_icon='🕊️', layout='wide')
API=os.getenv('VAULT_API_URL','http://127.0.0.1:8000').rstrip('/')
HEADERS={'X-API-Key':os.getenv('VAULT_API_KEY')} if os.getenv('VAULT_API_KEY') else {}
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:Inter,sans-serif}.stApp{background:linear-gradient(135deg,#080a10,#111722 55%,#090b11);color:#e8edf7}
#MainMenu,footer,header{visibility:hidden}.block-container{padding-top:1.2rem;max-width:1500px}
.brand{font-size:28px;font-weight:800;color:white;letter-spacing:-1px}.muted{color:#91a0b5}
.hero{padding:34px;border:1px solid #26364e;border-radius:22px;background:linear-gradient(110deg,rgba(37,99,235,.23),rgba(15,23,42,.4));margin:14px 0 24px}
.hero h1{font-size:38px;color:white;font-weight:800;margin:0}.card{background:#121925;border:1px solid #263244;border-radius:15px;padding:14px;margin-bottom:12px}
div[data-testid="stMetric"]{background:#121925;border:1px solid #263244;padding:15px;border-radius:14px}
.stButton>button{border-radius:10px;border:1px solid #334155;background:#17263d;color:white}
</style>''',unsafe_allow_html=True)
def get(path,params=None):
    try:
        r=requests.get(API+path,params=params,headers=HEADERS,timeout=18);r.raise_for_status();return r.json()
    except Exception as e: st.error(f'API connection issue: {e}');return {}
def data(p): return p.get('data',p) if isinstance(p,dict) else p
with st.sidebar:
    st.markdown('## 🕊️ WRLD VAULT')
    page=st.radio('NAVIGATION',['Home','Tracker','Discography','Eras','Snippets','Grails','Radio','Charts','Group Buys','Producers & Engineers','Community','API'])
    st.caption('V2 · The archive')
st.markdown('<div class="brand">🕊️ JUICE WRLD VAULT <span class="muted">V2</span></div><div class="muted">The archive. The music. The legacy.</div>',unsafe_allow_html=True)
if page=='Home':
    stats=data(get('/api/v1/stats'));st.markdown('<div class="hero"><span class="muted">THE WRLD ARCHIVE</span><h1>Keep the WRLD alive.</h1><p class="muted">Explore songs, releases, eras, credits and the music archive.</p></div>',unsafe_allow_html=True)
    if isinstance(stats,dict) and stats:
        cols=st.columns(5)
        for c,label,key in zip(cols,['Songs','Versions','Studio sessions','Eras','People'],['songs','versions','studioSessions','eras','people']):c.metric(label,f'{stats.get(key,0):,}')
    q=st.text_input('Search the Vault',placeholder='Search songs, eras, projects or people...')
    if q:
        result=data(get('/api/v1/search',{'q':q,'limit':12}));
        for s in result.get('songs',[])[:12]: st.markdown(f'<div class="card"><b>{html.escape(s.get("title","Unknown"))}</b><br><span class="muted">{html.escape(str(s.get("status",""))).upper()} · {html.escape(str(s.get("era") or "Unknown era"))}</span><br><a href="{html.escape(s.get("url","#"))}" target="_blank">Open song ↗</a></div>',unsafe_allow_html=True)
elif page=='Tracker':
    st.subheader('🎵 Song Tracker');a,b,c=st.columns([2,1,1]);q=a.text_input('Search songs');status=b.selectbox('Status',['All','released','leaked','unsurfaced','session','misc']);limit=c.selectbox('Page size',[25,50,100,200],index=1)
    params={'limit':limit};
    if q:params['q']=q
    if status!='All':params['status']=status
    payload=get('/api/v1/songs',params);items=data(payload)
    if isinstance(items,list):
        st.caption(f'{payload.get("meta",{}).get("total",len(items)):,} total entries · {len(items)} shown')
        for s in items:
            left,right=st.columns([1,5])
            if s.get('cover'):left.image(s['cover'],use_container_width=True)
            right.markdown(f'**{s.get("title","Unknown")}**');right.caption(f'{str(s.get("status","")).upper()} · {s.get("era") or "Unknown era"} · {(s.get("duration") or {}).get("text","")}');right.markdown(f'[Open song page]({s.get("url","#")})');st.divider()
elif page=='Discography':
    st.subheader('💿 Discography');items=data(get('/api/v1/projects'));items=items.get('projects',items.get('data',[])) if isinstance(items,dict) else items
    if isinstance(items,list):
        for p in items:
            with st.container(border=True):
                x,y=st.columns([1,4]);
                if p.get('cover'):x.image(p['cover'],use_container_width=True)
                y.markdown(f'### {p.get("name","Release")}');y.caption(f'{p.get("kind","Release")} · {p.get("era","")} · {p.get("trackCount","")} tracks');
                if p.get('url'):y.markdown(f'[Open release ↗]({p["url"]})')
elif page=='Eras':
    st.subheader('🕰️ Eras');items=data(get('/api/v1/eras'));items=items.get('eras',items.get('data',[])) if isinstance(items,dict) else items
    if isinstance(items,list):
        for e in items:
            with st.container(border=True):
                if e.get('cover'):st.image(e['cover'],width=180)
                st.markdown(f'### {e.get("name",e.get("code","Era"))}');st.caption(f'{(e.get("counts") or {}).get("songs",0)} songs · {(e.get("counts") or {}).get("versions",0)} versions')
                if e.get('url'):st.markdown(f'[Explore era ↗]({e["url"]})')
elif page=='Producers & Engineers':
    st.subheader('🎚️ Producers & Engineers');q=st.text_input('Find a person');items=data(get('/api/v1/people'));items=items.get('people',items.get('data',[])) if isinstance(items,dict) else items
    if isinstance(items,list):
        for p in items:
            if q.lower() in p.get('name','').lower():st.markdown(f'- **{p.get("name","Unknown")}** · {p.get("songs",0)} songs · [Profile]({p.get("url","#")})')
elif page=='Radio':
    st.subheader('📻 WRLD Radio')
    if st.button('Get random song'):st.json(data(get('/api/v1/radio/random')))
    st.info('Random-song endpoint is connected. Full persistent playback queue is the next player integration.')
elif page in ['Snippets','Grails','Charts','Group Buys','Community']:
    st.subheader({'Snippets':'🎬 Snippets & footage','Grails':'🏆 Grails','Charts':'📊 Charts','Group Buys':'💰 Group buys','Community':'💬 Community'}[page])
    st.info('Navigation and page scaffold are ready. These datasets are not included in the documented juicewrld.io v1 endpoints; we will connect them when their exact juicewrldapi.com routes/JSON shapes are confirmed.')
elif page=='API':
    st.subheader('🔌 Developer API');st.write('Bot API base URL:');st.code('https://YOUR-DOMAIN/api/v1');st.write('Interactive docs:');st.code('https://YOUR-DOMAIN/docs');st.code('''GET /api/v1/search?q=lucid
GET /api/v1/songs?status=leaked&limit=50
GET /api/v1/songs/{song_id}
GET /api/v1/eras
GET /api/v1/projects
GET /api/v1/people
GET /api/v1/stats
GET /api/v1/media/search?q=lucid
GET /api/v1/radio/random''',language='http')
