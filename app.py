import streamlit as st
from groq import Groq
import json
import os
from io import BytesIO
from md2pdf.core import md2pdf
import random

# Initialize session state variables
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get("GROQ_API_KEY", "")

if 'groq' not in st.session_state:
    st.session_state.groq = None

class GenerationStatistics:
    # ... [The rest of the GenerationStatistics class remains unchanged]

class Story:
    # ... [The rest of the Story class remains unchanged]

def create_markdown_file(content: str) -> BytesIO:
    # ... [This function remains unchanged]

def create_pdf_file(content: str):
    # ... [This function remains unchanged]

def generate_story_structure(title: str, genre: str, theme: str, num_chapters: int):
    if not st.session_state.groq:
        raise ValueError("Groq client is not initialized. Please enter a valid API key.")
    
    # ... [The rest of this function remains unchanged]

def generate_chapter(chapter_title: str, chapter_summary: str, characters: list, setting: str, style: str):
    if not st.session_state.groq:
        raise ValueError("Groq client is not initialized. Please enter a valid API key.")
    
    # ... [The rest of this function remains unchanged]

def generate_character():
    # ... [This function remains unchanged]

# Streamlit UI
st.title("Novel-Style Story Generator")

with st.sidebar:
    # API Key Input
    api_key = st.text_input("Enter your Groq API Key (gsk_...):", st.session_state.api_key, type="password")
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        if api_key:
            try:
                st.session_state.groq = Groq(api_key=api_key)
                st.success("API key set successfully!")
            except Exception as e:
                st.error(f"Error initializing Groq client: {str(e)}")
                st.session_state.groq = None
        else:
            st.session_state.groq = None

    # Story details inputs
    story_title = st.text_input("Enter a title for your story:", "")
    genre = st.selectbox("Select a genre:", ["Science Fiction", "Fantasy", "Mystery", "Romance", "Horror", "Thriller", "Historical Fiction", "Comedy"])
    theme = st.text_input("Enter a theme for your story:", "")
    num_chapters = st.slider("Number of chapters:", 3, 20, 10)
    writing_style = st.selectbox("Select a writing style:", ["Descriptive", "
