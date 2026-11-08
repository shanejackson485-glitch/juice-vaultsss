import streamlit as st
from core.ui import theme, render_sidebar, render_header
from core.services import services
from core.pages import PAGES

st.set_page_config(page_title="Vanta • Bot Studio", page_icon="◈", layout="wide")
theme()
svc = services()
render_header()
page = render_sidebar(svc)
PAGES[page](svc)
if svc.process.running:
    st.markdown("<meta http-equiv='refresh' content='2'>", unsafe_allow_html=True)
