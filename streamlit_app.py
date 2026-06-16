import streamlit as st
import streamlit.components.v1 as components
import os
import time
from pathlib import Path

st.set_page_config(
    page_title="AICA | Personalized Clinical Reasoning",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Nuke every piece of Streamlit chrome: header, footer, sidebar toggle,
# padding, scrollbars — let our HTML control everything.
st.markdown("""
<style>
  /* Hide all Streamlit UI decorations */
  [data-testid="stHeader"]         { display: none !important; }
  [data-testid="stToolbar"]        { display: none !important; }
  [data-testid="stSidebarNav"]     { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }
  #MainMenu, footer, header        { display: none !important; }

  /* Kill all page padding/margin so iframe fills the window */
  .appview-container, .main, .block-container,
  [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      padding: 0 !important;
      margin: 0 !important;
      max-width: 100vw !important;
  }

  /* Make the iframe itself full-screen */
  iframe {
      border: none;
      display: block;
      width: 100vw;
      height: 100vh;
      position: fixed;
      top: 0;
      left: 0;
      z-index: 9999;
  }
</style>
""", unsafe_allow_html=True)

# Read backend URL from environment; default to localhost for local testing
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# simple cache buster so HTML/CSS updates show immediately in hosted environments
_CACHE_BUST = int(time.time())

# debug banner so deployed app shows which BACKEND_URL and cache token it's using
try:
    import streamlit as st
    st.markdown(f"<div style='position:fixed;right:8px;top:8px;z-index:9999;padding:6px 8px;border-radius:6px;background:#fff;border:1px solid #eee;font-size:12px'>BACKEND_URL: {BACKEND_URL} - v:{_CACHE_BUST}</div>", unsafe_allow_html=True)
except Exception:
    pass

html_path = Path(__file__).parent / "frontend" / "streamlit_index.html"
html_code = html_path.read_text(encoding="utf-8")
html_code = html_code.replace("BACKEND_URL_PLACEHOLDER", BACKEND_URL)

# Use screen height to fill viewport; scrolling=False because our app
# manages its own scrolling internally.
components.html(html_code, height=1080, scrolling=False)
