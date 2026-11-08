import streamlit as st

NAV = {
    "CONTROL ROOM": ["Overview", "Console", "Startup"],
    "BUILD & TOOLS": ["Templates", "Files", "Tools"],
    "CONFIGURATION": ["Environment", "Backups", "Settings", "Documentation"]
}

def theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    :root{--bg:#111112;--surface:#242427;--border:#34343a;--muted:#9299a6;--text:#e8eaf0;--accent:#a100ff}
    html,body,[data-testid="stAppViewContainer"]{background:var(--bg);color:var(--text);font-family:Inter,system-ui}
    [data-testid="stSidebar"]{background:#171719;border-right:1px solid var(--border)}
    .block-container{max-width:1450px;padding:1.6rem 2rem 5rem}
    h1{font-size:2.55rem!important;font-weight:900!important;letter-spacing:-.05em}
    h2,h3{font-weight:800!important}
    [data-testid="stMetric"]{background:var(--surface);border:1px solid var(--border);border-radius:17px;padding:18px}
    [data-testid="stMetricLabel"]{color:var(--muted)!important;font-weight:800}
    [data-testid="stMetricValue"]{color:var(--text)!important;font-weight:900}
    .stButton>button,.stDownloadButton>button{background:#353c4a;color:white;border:1px solid #454b59;border-radius:11px;font-weight:800;min-height:2.7rem}
    .stButton>button[kind="primary"]{background:var(--accent);border-color:var(--accent)}
    input,textarea,[data-baseweb="select"]>div{background:#252528!important;color:var(--text)!important;border:1px solid #414149!important;border-radius:10px!important}
    .hero{background:linear-gradient(120deg,#2a1039,#202024 65%,#19191b);border:1px solid #48265c;border-radius:21px;padding:25px;margin-bottom:20px}
    .kicker,.eyebrow{font-size:.75rem;letter-spacing:.12em;font-weight:900;color:#c58af0}
    .hero-title{font-size:1.65rem;font-weight:900;margin:5px 0}
    .muted{color:var(--muted)!important}
    .card,.file-row{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:18px;margin:7px 0}
    .logbox{background:#080809;border:1px solid #303036;border-radius:14px;padding:14px;height:490px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,Menlo,monospace}
    .log-error{color:#ff8585}.log-warn{color:#ffc45c}.log-info{color:#e5e8ee}
    .dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#25c76f;margin-right:8px}.dot.off{background:#777e89}
    hr{border-color:var(--border)!important}
    @media(max-width:700px){.block-container{padding:1rem}.hero{padding:17px}.logbox{height:370px}}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown("<div class='hero'><div class='kicker'>◈ VANTA / LOCAL DEVELOPMENT ENVIRONMENT</div><div class='hero-title'>Discord Bot Studio</div><div class='muted'>A control room for bot projects, processes, templates and developer tools.</div></div>", unsafe_allow_html=True)

def render_sidebar(svc):
    with st.sidebar:
        st.markdown("## ◈ VANTA")
        st.caption("DISCORD BOT STUDIO")
        current=st.session_state.get("nav","Overview")
        for group, pages in NAV.items():
            st.markdown(f"<div class='eyebrow'>{group}</div>",unsafe_allow_html=True)
            for name in pages:
                if st.button(("◆  " if current==name else "　")+name,key="nav_"+name,use_container_width=True):
                    st.session_state["nav"]=name
                    st.rerun()
        st.divider()
        folder=st.text_input("PROJECT FOLDER",svc.settings.get("project"))
        if folder!=svc.settings.get("project"):
            svc.settings.set_many(project=folder)
        state=svc.process.status()
        st.markdown(f"<div class='card'><div class='eyebrow'>PROCESS STATUS</div><b><span class='dot {' ' if state['running'] else 'off'}'></span>{'ONLINE' if state['running'] else 'OFFLINE'}</b><br><span class='muted'>PID {state['pid'] or '—'}</span></div>",unsafe_allow_html=True)
    return st.session_state.get("nav","Overview")
