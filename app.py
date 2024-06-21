import streamlit as st
from groq import Groq
import json
import os
from io import BytesIO
from md2pdf.core import md2pdf
import random

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", None)

if 'api_key' not in st.session_state:
    st.session_state.api_key = GROQ_API_KEY

if 'groq' not in st.session_state:
    if GROQ_API_KEY:
        st.session_state.groq = Groq()

class GenerationStatistics:
    def __init__(self, input_time=0, output_time=0, input_tokens=0, output_tokens=0, total_time=0, model_name="llama3-8b-8192"):
        self.input_time = input_time
        self.output_time = output_time
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_time = total_time
        self.model_name = model_name

    def get_input_speed(self):
        return self.input_tokens / self.input_time if self.input_time != 0 else 0
    
    def get_output_speed(self):
        return self.output_tokens / self.output_time if self.output_time != 0 else 0
    
    def add(self, other):
        if not isinstance(other, GenerationStatistics):
            raise TypeError("Can only add GenerationStatistics objects")
        
        self.input_time += other.input_time
        self.output_time += other.output_time
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_time += other.total_time

    def __str__(self):
        return (f"\n## {self.get_output_speed():.2f} T/s ⚡\nRound trip time: {self.total_time:.2f}s  Model: {self.model_name}\n\n"
                f"| Metric          | Input          | Output          | Total          |\n"
                f"|-----------------|----------------|-----------------|----------------|\n"
                f"| Speed (T/s)     | {self.get_input_speed():.2f}            | {self.get_output_speed():.2f}            | {(self.input_tokens + self.output_tokens) / self.total_time if self.total_time != 0 else 0:.2f}            |\n"
                f"| Tokens          | {self.input_tokens}            | {self.output_tokens}            | {self.input_tokens + self.output_tokens}            |\n"
                f"| Inference Time (s) | {self.input_time:.2f}            | {self.output_time:.2f}            | {self.total_time:.2f}            |")

class Story:
    def __init__(self, structure, characters, setting):
        self.structure = structure
        self.characters = characters
        self.setting = setting
        self.contents = {f"Chapter {i+1}": "" for i in range(len(structure) - 1)}  # -1 to exclude 'title'
        self.placeholders = {f"Chapter {i+1}": st.empty() for i in range(len(structure) - 1)}

        st.markdown("## Novel Structure:")
        for i, (chapter, summary) in enumerate(structure.items()):
            if chapter != 'title':
                st.markdown(f"### Chapter {i}: {summary}")
        st.markdown("---")

    def update_content(self, chapter, new_content):
        self.contents[chapter] += new_content
        self.display_content(chapter)

    def display_content(self, chapter):
        if self.contents[chapter].strip():
            self.placeholders[chapter].markdown(f"## {chapter}\n{self.contents[chapter]}")

    def get_markdown_content(self):
        markdown_content = f"# {self.structure['title']}\n\n"
        markdown_content += f"## Setting\n{self.setting}\n\n"
        markdown_content += "## Main Characters\n"
        for char in self.characters:
            markdown_content += f"- {char['name']}: {char['description']}\n"
        markdown_content += "\n"
        for chapter, content in self.contents.items():
            markdown_content += f"## {chapter}\n{content}\n\n"
        return markdown_content

def create_markdown_file(content: str) -> BytesIO:
    markdown_file = BytesIO()
    markdown_file.write(content.encode('utf-8'))
    markdown_file.seek(0)
    return markdown_file

def create_pdf_file(content: str):
    pdf_buffer = BytesIO()
    md2pdf(pdf_buffer, md_content=content)
    pdf_buffer.seek(0)
    return pdf_buffer

def generate_story_structure(title: str, genre: str, theme: str, num_chapters: int):
    completion = st.session_state.groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": "Generate a novel structure with chapter summaries."
            },
            {
                "role": "user",
                "content": f"Create a {num_chapters}-chapter novel structure for a {genre} story titled '{title}' with the theme of '{theme}'. Provide a brief summary for each chapter. Return the result as a JSON object where each key is a chapter number (except for the 'title' key) and the value is the chapter summary."
            }
        ],
        temperature=0.7,
        max_tokens=8000,
        top_p=1,
        stream=False,
    )

    usage = completion.usage
    statistics = GenerationStatistics(input_time=usage.prompt_time, output_time=usage.completion_time, 
                                      input_tokens=usage.prompt_tokens, output_tokens=usage.completion_tokens, 
                                      total_time=usage.total_time, model_name="llama3-70b-8192")

    structure = json.loads(completion.choices[0].message.content)
    structure['title'] = title
    return statistics, structure

def generate_chapter(chapter_title: str, chapter_summary: str, characters: list, setting: str, style: str):
    stream = st.session_state.groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": f"You are an expert novelist writing in a {style} style. Generate an engaging chapter based on the provided information."
            },
            {
                "role": "user",
                "content": f"Write a detailed chapter for a novel with the following information:\nTitle: {chapter_title}\nSummary: {chapter_summary}\nCharacters: {', '.join([c['name'] for c in characters])}\nSetting: {setting}\n\nInclude character interactions and dialogue where appropriate."
            }
        ],
        temperature=0.7,
        max_tokens=8000,
        top_p=1,
        stream=True,
    )

    for chunk in stream:
        tokens = chunk.choices[0].delta.content
        if tokens:
            yield tokens
        if x_groq := chunk.x_groq:
            if not x_groq.usage:
                continue
            usage = x_groq.usage
            statistics = GenerationStatistics(input_time=usage.prompt_time, output_time=usage.completion_time,
                                              input_tokens=usage.prompt_tokens, output_tokens=usage.completion_tokens,
                                              total_time=usage.total_time, model_name="llama3-8b-8192")
            yield statistics

def generate_character():
    names = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah"]
    backgrounds = ["mysterious past", "wealthy upbringing", "humble beginnings", "tragic childhood"]
    traits = ["brave", "intelligent", "cunning", "compassionate", "ambitious", "reserved"]
    
    return {
        "name": random.choice(names),
        "description": f"A {random.choice(traits)} individual with a {random.choice(backgrounds)}."
    }

# Streamlit UI
st.title("Novel-Style Story Generator")

with st.sidebar:
    if not GROQ_API_KEY:
        groq_input_key = st.text_input("Enter your Groq API Key (gsk_yA...):", "", type="password")

    story_title = st.text_input("Enter a title for your story:", "")
    genre = st.selectbox("Select a genre:", ["Science Fiction", "Fantasy", "Mystery", "Romance", "Horror", "Thriller", "Historical Fiction", "Comedy"])
    theme = st.text_input("Enter a theme for your story:", "")
    num_chapters = st.slider("Number of chapters:", 3, 20, 10)
    writing_style = st.selectbox("Select a writing style:", ["Descriptive", "Concise", "Poetic", "Humorous"])

    st.subheader("Characters")
    num_characters = st.number_input("Number of characters:", 1, 5, 2)
    characters = []
    for i in range(num_characters):
        st.markdown(f"### Character {i+1}")
        if st.button(f"Generate Random Character {i+1}"):
            characters.append(generate_character())
        else:
            name = st.text_input(f"Name for Character {i+1}:", key=f"char_name_{i}")
            description = st.text_area(f"Description for Character {i+1}:", key=f"char_desc_{i}")
            if name and description:
                characters.append({"name": name, "description": description})

    setting = st.text_area("Describe the story's setting:")

    generate_button = st.button("Generate Novel")

# Main content area
if 'story' in st.session_state:
    story = st.session_state.story
    st.markdown(f"# {story.structure['title']}")
    st.markdown(f"## Setting\n{story.setting}")
    st.markdown("## Main Characters")
    for char in story.characters:
        st.markdown(f"- **{char['name']}**: {char['description']}")

    progress_bar = st.progress(0)
    for i, (chapter, content) in enumerate(story.contents.items()):
        story.display_content(chapter)
        progress_bar.progress((i + 1) / len(story.contents))

    if st.button('Download Novel'):
        markdown_file = create_markdown_file(story.get_markdown_content())
        st.download_button(
            label='Download as Markdown',
            data=markdown_file,
            file_name='generated_novel.md',
            mime='text/markdown'
        )

        pdf_file = create_pdf_file(story.get_markdown_content())
        st.download_button(
            label='Download as PDF',
            data=pdf_file,
            file_name='generated_novel.pdf',
            mime='application/pdf'
        )

elif generate_button:
    if not story_title or not theme or not setting or len(characters) == 0:
        st.error("Please fill in all required fields (title, theme, setting, and at least one character).")
    else:
        with st.spinner("Generating novel structure..."):
            structure_stats, structure = generate_story_structure(story_title, genre, theme, num_chapters)
            story = Story(structure, characters, setting)
            st.session_state.story = story

        total_stats = GenerationStatistics()

        for i, (chapter, summary) in enumerate(structure.items()):
            if chapter != 'title':
                with st.spinner(f"Generating Chapter {i}..."):
                    content_stream = generate_chapter(f"Chapter {i}", summary, characters, setting, writing_style)
                    for chunk in content_stream:
                        if isinstance(chunk, GenerationStatistics):
                            total_stats.add(chunk)
                        else:
                            story.update_content(f"Chapter {i}", chunk)

        st.success("Novel generation complete!")
        st.markdown(str(total_stats))

else:
    st.write("Fill in the details in the sidebar and click 'Generate Novel' to create your story.")
