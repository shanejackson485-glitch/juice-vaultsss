import streamlit as st
import psutil
import subprocess
import os
import time

st.set_page_config(page_title="Bot Dashboard", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR PURPLE UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0d0f12; color: #e0e0e0; }
    
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .block-container { padding-top: 2rem; max-width: 1000px; }

    /* Top Nav */
    .nav-bar {
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(26, 29, 36, 0.7); backdrop-filter: blur(10px);
        padding: 15px 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .nav-title { color: white; font-size: 24px; font-weight: 800; margin: 0; display: flex; align-items: center; gap: 10px; }

    /* Cards */
    .card {
        background: #15171e; border-radius: 16px; border: 1px solid #2a2e39;
        padding: 25px; margin-bottom: 20px;
    }
    .card-title { color: white; font-size: 20px; font-weight: 800; margin-bottom: 15px; }

    /* Stats */
    .stat-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; font-weight: 600; color: #9ca3af; }
    .stat-value { color: white; }
    .progress-bg { background: #2a2e39; height: 10px; border-radius: 5px; overflow: hidden; margin-bottom: 20px; }
    .progress-fill { height: 100%; border-radius: 5px; transition: width 0.5s ease; }
    .bg-blue { background: #3b82f6; }
    .bg-purple { background: #8b5cf6; }
    .bg-green { background: #10b981; }

    /* Status Dot */
    .status-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 10px; }
    .dot-online { background: #10b981; box-shadow: 0 0 10px #10b981; }
    .dot-offline { background: #ef4444; box-shadow: 0 0 10px #ef4444; }

    /* Buttons */
    .stButton > button {
        border-radius: 12px !important; font-weight: 700 !important; border: none !important;
        width: 100%; padding: 12px !important; transition: 0.2s; color: white !important;
    }
    .stButton > button:hover { transform: scale(1.02); }
    
    /* Specific Button Colors */
    div[data-testid="stButton"] button[kind="primary"] { background: #8b5cf6 !important; }
    div[data-testid="stButton"] button[kind="primary"]:hover { background: #7c3aed !important; }
    
    div[data-testid="stButton"] button[kind="secondary"] { background: #ef4444 !important; }
    div[data-testid="stButton"] button[kind="secondary"]:hover { background: #dc2626 !important; }
</style>
""", unsafe_allow_html=True)

# --- BOT PROCESS CHECKER ---
BOT_SCRIPT = "bot.py" # CHANGE THIS to your actual bot file name

def is_bot_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and BOT_SCRIPT in " ".join(cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

# --- UI START ---
st.markdown("""
<div class="nav-bar">
    <div class="nav-title">🤖 Bot Dashboard</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

# --- LEFT COLUMN: STATS & GITHUB ---
with col1:
    # Server Stats
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Server Status</div>', unsafe_allow_html=True)
    
    # Status dot
    running = is_bot_running()
    if running:
        st.markdown('<div style="margin-bottom: 20px;"><span class="status-dot dot-online"></span><span style="color: #10b981; font-weight: bold;">Bot is Online</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin-bottom: 20px;"><span class="status-dot dot-offline"></span><span style="color: #ef4444; font-weight: bold;">Bot is Offline</span></div>', unsafe_allow_html=True)

    # Get Stats
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    # Render Bars
    st.markdown(f'''
        <div class="stat-row"><span>CPU Load</span> <span class="stat-value">{cpu}%</span></div>
        <div class="progress-bg"><div class="progress-fill bg-blue" style="width: {cpu}%"></div></div>
        
        <div class="stat-row"><span>Memory</span> <span class="stat-value">{ram}%</span></div>
        <div class="progress-bg"><div class="progress-fill bg-purple" style="width: {ram}%"></div></div>
        
        <div class="stat-row"><span>Disk Space</span> <span class="stat-value">{disk}%</span></div>
        <div class="progress-bg"><div class="progress-fill bg-green" style="width: {disk}%"></div></div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # GitHub Integration
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">GitHub Integration</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 15px;">Pull the latest code from your repository to update the bot.</p>', unsafe_allow_html=True)
    
    if st.button("Pull Latest Code from GitHub", type="primary"):
        with st.spinner("Pulling from GitHub..."):
            try:
                # Run git pull
                result = subprocess.run(["git", "pull"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("✅ Successfully pulled code!")
                    st.code(result.stdout)
                else:
                    st.error("❌ Failed to pull code.")
                    st.code(result.stderr)
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- RIGHT COLUMN: CONTROLS ---
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Bot Controls</div>', unsafe_allow_html=True)
    
    if st.button("Restart Bot", type="primary"):
        with st.spinner("Restarting..."):
            try:
                # Kill existing bot
                for proc in psutil.process_iter(['name', 'cmdline']):
                    cmdline = proc.info['cmdline']
                    if cmdline and BOT_SCRIPT in " ".join(cmdline):
                        proc.kill()
                
                # Start bot
                subprocess.Popen(["python", BOT_SCRIPT])
                st.success("✅ Bot Restarted!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("Stop Bot", type="secondary"):
        with st.spinner("Stopping..."):
            try:
                for proc in psutil.process_iter(['name', 'cmdline']):
                    cmdline = proc.info['cmdline']
                    if cmdline and BOT_SCRIPT in " ".join(cmdline):
                        proc.kill()
                        st.success("✅ Bot Stopped!")
                        time.sleep(1)
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
                
    st.markdown('</div>', unsafe_allow_html=True)