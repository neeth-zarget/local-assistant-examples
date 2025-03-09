import os
import time
import tempfile
import streamlit as st
from streamlit_chat import message
from ChatBooks import ChatBooks
from config import Config
from helpers import *
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import asyncio
from mindmap_page import page as mindmap_page

st.set_page_config(page_title="ChatBooks")

def get_chat_books_assistant():
    return ChatBooks(llm_model="llama3.2")

def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        message(msg, is_user=is_user, key=str(i))
    st.session_state["thinking_spinner"] = st.empty()

    with st.expander("Question, Answer and Add to QA Store", expanded=False):
        question = st.text_input("Question", key="question")
        answer = st.text_area("Answer", key="answer")

        if st.button("Add to QA store"):
            st.session_state["assistant"].store_qa(question, answer)
            st.success("Question and answer stored successfully!")

def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        st.session_state["messages"].append((user_text, True))

        with st.session_state["thinking_spinner"], st.spinner("Thinking"):
            agent_text = st.session_state["assistant"].ask(user_text)

        st.session_state["messages"].append((agent_text, False))
        st.session_state["user_input"] = ""

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recv(self, frame):
        audio_data = frame.to_ndarray()
        audio = sr.AudioData(audio_data.tobytes(), frame.sample_rate, frame.sample_width)
        try:
            user_text = self.recognizer.recognize_google(audio)
            st.session_state["messages"].append((user_text, True))

            with st.session_state["thinking_spinner"], st.spinner("Thinking"):
                agent_text = st.session_state["assistant"].ask(user_text)

            st.session_state["messages"].append((agent_text, False))

            # Convert response to audio
            tts = gTTS(text=agent_text, lang='en')
            tts.save("response.mp3")
            audio_response = AudioSegment.from_mp3("response.mp3")
            play(audio_response)
        except sr.UnknownValueError:
            st.error("Google Speech Recognition could not understand the audio")
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")

def read_and_save_files_from_dir(directory):
    if "files_ingested" not in st.session_state:
        st.session_state["files_ingested"] = set()

    st.session_state["assistant"].clear()
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        processed_file_path = os.path.join(Config.BOOKS_PROCESSED_DIR, get_processed_file_name(filename))
        if os.path.isfile(file_path) and filename not in st.session_state["files_ingested"]:
            if file_path.endswith(".pdf") and os.path.exists(processed_file_path):
                continue  # Skip already ingested PDFs
            with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {filename}"):
                t0 = time.time()
                st.session_state["assistant"].ingest(file_path)
                t1 = time.time()

            st.session_state["files_ingested"].add(filename)

def display_files(directory):
    st.subheader("Files in Books Directory")
    files = os.listdir(directory)
    for i, file in enumerate(files, start=1):
        st.markdown(f"{i}. {file}")

async def main():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "assistant" not in st.session_state:
        st.session_state["assistant"] = get_chat_books_assistant()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["ChatBooks", "MindMap"])

    if page == "ChatBooks":
        st.header("ChatBooks")

        st.session_state["ingestion_spinner"] = st.empty()

        # Load files from directory
        directory = Config.BOOKS_DIR
        read_and_save_files_from_dir(directory)

        display_files(directory)
        display_messages()
        st.text_input("Message", key="user_input", on_change=process_input)

        webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioProcessor,
            media_stream_constraints={"audio": True, "video": False}
        )
    elif page == "MindMap":
        mindmap_page()

if __name__ == "__main__":
    create_data_sub_dirs_if_not_exists()
    asyncio.run(main())