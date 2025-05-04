import streamlit as st
import google.generativeai as genai
import threading
import speech_recognition as sr
import os
from dotenv import load_dotenv
import comtypes
import pyttsx3

# -- Initialization --
comtypes.CoInitialize()
load_dotenv()

# Page config must be first Streamlit call
st.set_page_config(page_title="Voice-First Indoor Navigator", layout="centered")
st.title("🎤 Voice-First Bathroom Navigator")

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    st.error("Please set your GOOGLE_API_KEY in .env")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Text-to-Speech Setup (fresh engine each time)
def _speak(text: str):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

def speak(text: str):
    threading.Thread(target=_speak, args=(text,), daemon=True).start()

# System Prompt
SYSTEM_PROMPT = (
    "You are a smart indoor navigation assistant for a bathroom divided into four 1m² areas: "
    "Shower area at (0,0), Basin area at (1,0), Entrance area at (0,1), Toilet area at (1,1). "
    "Provide concise step-by-step navigation commands: Move Left, Move Right, Move Forward, Move Backward. "
    "Always consider the user's current location and target, and ask clarifying questions if needed."
)

# Segments Map
def load_segments():
    return {
        "Shower":   (0, 0),
        "Basin":    (1, 0),
        "Entrance": (0, 1),
        "Toilet":   (1, 1),
    }
SEGMENTS = load_segments()

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "last_assistant" not in st.session_state:
    st.session_state.last_assistant = ""
if "current_loc" not in st.session_state:
    st.session_state.current_loc = "Entrance"

# Process command via Gemini
def process_command(user_text: str):
    st.session_state.messages.append({"role": "user", "content": user_text})
    # Build prompt: system+location+history
    prompt_parts = []
    prompt_parts.append(SYSTEM_PROMPT)
    prompt_parts.append(f"I am currently at the {st.session_state.current_loc}.")
    for m in st.session_state.messages[1:]:
        prompt_parts.append(m['content'])
    # Format for Gemini
    formatted = [{"role":"user","parts":[{"text":part}]} for part in prompt_parts]
    try:
        resp = model.generate_content(formatted, generation_config={"temperature":0.3})
        reply = resp.text
    except Exception:
        reply = "Sorry, I couldn't process your request."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_assistant = reply
    speak(reply)

# Listen-and-respond
def listen_and_respond():
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            st.info("Listening...")
            audio = recognizer.listen(source, phrase_time_limit=5)
        user_text = recognizer.recognize_google(audio)
        process_command(user_text)
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
    except sr.RequestError:
        speak("Speech recognition service error.")
    except Exception as e:
        st.warning(f"Microphone or recognition error: {e}")

# Sidebar: manual location debug
debug = st.sidebar.checkbox("Debug Mode: Set Location Manually")
if debug:
    loc = st.sidebar.selectbox(
        "Current Location:", list(SEGMENTS.keys()),
        index=list(SEGMENTS.keys()).index(st.session_state.current_loc)
    )
    if loc != st.session_state.current_loc:
        st.session_state.current_loc = loc
        msg = f"Location manually set to {loc}."
        st.session_state.messages.append({"role": "user", "content": msg})
        speak(msg)
else:
    st.sidebar.info("Press 'Start Listening' below to issue a voice command.")

# Start Listening Button
if st.button("🎙️ Start Listening"):
    listen_and_respond()

# Display Map
st.subheader("🗺️ Bathroom Map")
rows = [["Shower","Basin"],["Entrance","Toilet"]]
for row in rows:
    line = [f"📍{name}" if name==st.session_state.current_loc else name for name in row]
    st.text("   ".join(line))

# Repeat and Clear controls
col1, col2 = st.columns(2)
with col1:
    if st.button("🔊 Repeat Last") and st.session_state.last_assistant:
        speak(st.session_state.last_assistant)
with col2:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.last_assistant = ""

# Transcript
st.subheader("💬 Conversation Transcript")
for m in st.session_state.messages:
    prefix = "**You:**" if m['role']=='user' else "**Assistant:**"
    st.markdown(f"{prefix} {m['content']}")
