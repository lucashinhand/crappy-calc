import streamlit as st
import os

CUSTOM_TITLE = os.getenv("CUSTOM_TITLE", "Crappy Calculator")

st.set_page_config(
    page_title=CUSTOM_TITLE,
    page_icon="📈",
    layout="wide"
)

ADMIN_ENABLED = os.getenv("ADMIN_ENABLED", "false").lower() == "true"

regular_pages = ["pages/calc.py"]

admin_pages = [st.Page("pages/calc.py", title="Calculator"), st.Page("pages/config.py", title="Config")]

position = "sidebar" if ADMIN_ENABLED else "hidden"
pages = regular_pages if not ADMIN_ENABLED else admin_pages

pg = st.navigation(pages, position=position)
pg.run()