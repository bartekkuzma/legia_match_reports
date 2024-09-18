import re

import streamlit as st


class Toc:

    def __init__(self):
        self._items = []
        self._placeholder = None
    
    def title(self, text):
        self._markdown(text, "h1")

    def header(self, text):
        self._markdown(text, "h2")

    def subheader(self, text):
        self._markdown(text, "h3")

    def placeholder(self, sidebar=False):
        self._placeholder = st.sidebar.empty() if sidebar else st.empty()

    def generate(self):
        if self._placeholder:
            toc_md = "\n".join(self._items)
            self._placeholder.markdown(toc_md, unsafe_allow_html=True)

    def _markdown(self, text, level):
        # Create a unique key for each header
        key = re.sub('[^0-9a-zA-Z]+', '-', text).lower()

        # Ensure header is displayed in the content
        st.markdown(f"<{level} id='{key}'>{text}</{level}>", unsafe_allow_html=True)

        # Add clickable entry in the Table of Contents
        self._items.append(f"* <a href='#{key}'>{text}</a>")
        