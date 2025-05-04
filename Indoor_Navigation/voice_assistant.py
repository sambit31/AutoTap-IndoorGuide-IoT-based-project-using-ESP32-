import streamlit as st
import google.generativeai as genai
import threading
import speech_recognition as sr
import os
from dotenv import load_dotenv
import comtypes
import pyttsx3
import requests

# -- Initialization --
comtypes.CoInitialize()
load_dotenv()

# Streamlit page config must come early
st.set_page_config(page_title="Voice-First Indoor Navigator", layout="centered")
st.title("🎤 Voice-First Bathroom Navigator & Pump Control")

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
ESP32_IP = os.getenv("ESP32_IP", "192.168.63.12")
if not GEMINI_API_KEY:
    st.error("Please set your GOOGLE_API_KEY in .env")
    st.stop()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Text-to-Speech (fresh engine each speak)
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
    "You are a smart indoor navigation and pump-control assistant for a bathroom divided into four 1m² zones: "
    "the Shower area (with shower head) at (0,0), Basin area (sink and vanity) at (1,0), "
    "Entrance area (doorway) at (0,1), and Toilet area (commode) at (1,1). "
    "When the user specifies a navigation destination, provide concise step-by-step commands: "
    "Move Left, Move Right, Move Forward, Move Backward. "
    "Additionally, you can control the bathroom pump: respond to 'pump on' or 'pump off' by initiating the respective command in the UI, "
    "and you can report pump status when asked. "
    "Always use area names, consider the user's current location and target, "
    "and ask clarifying questions if needed."
)

# Segments Map
SEGMENTS = {
    "Shower":   (0, 0),
    "Basin":    (1, 0),
    "Entrance": (0, 1),
    "Toilet":   (1, 1),
}

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
    parts = [SYSTEM_PROMPT, f"I am currently at the {st.session_state.current_loc}."]
    for msg in st.session_state.messages[1:]:
        parts.append(msg['content'])
    formatted = [{"role":"user","parts":[{"text":p}]} for p in parts]
    try:
        resp = model.generate_content(formatted, generation_config={"temperature":0.3})
        reply = resp.text
    except Exception:
        reply = "Sorry, I couldn't process your request."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.last_assistant = reply
    speak(reply)

# Listen-and-respond with spinner (clears after done)
def listen_and_respond():
    r = sr.Recognizer()
    with st.spinner("Listening ..."):
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src)
            audio = r.listen(src, phrase_time_limit=5)
        try:
            txt = r.recognize_google(audio)
            process_command(txt)
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
        except sr.RequestError:
            speak("Speech recognition service error.")
        except Exception as e:
            st.warning(f"Microphone error: {e}")

# Display map
st.subheader("🗺️ Bathroom Map")
for row in [["Shower","Basin"],["Entrance","Toilet"]]:
    line = [f"📍{n}" if n == st.session_state.current_loc else n for n in row]
    st.text("   ".join(line))

# Voice command
if st.button("🎙️ Start Listening"):
    listen_and_respond()

# Sidebar: Manual location & Pump control
with st.sidebar:
    st.header("Debug Mode")
    loc = st.selectbox("Set Current Location", list(SEGMENTS.keys()),
                       index=list(SEGMENTS.keys()).index(st.session_state.current_loc))
    if st.button("Update Location"):
        st.session_state.current_loc = loc
        msg = f"Location manually set to {loc}."
        st.session_state.messages.append({"role":"user","content":msg})
        speak(msg)
    st.markdown("---")
    st.header("Pump Control")
    if st.button("Pump ON"):
        try:
            requests.get(f"http://{ESP32_IP}/on", timeout=1)
        except:
            st.error("Failed to reach ESP32")
    if st.button("Pump OFF"):
        try:
            requests.get(f"http://{ESP32_IP}/off", timeout=1)
        except:
            st.error("Failed to reach ESP32")
    try:
        status = requests.get(f"http://{ESP32_IP}/status", timeout=1).text
        st.write(f"Pump status: **{status}**")
    except:
        st.write("Pump status: unknown")

# Conversation transcript
st.subheader("💬 Conversation Transcript")
for m in st.session_state.messages:
    prefix = "**You:**" if m['role'] == 'user' else "**Assistant:**"
    st.markdown(f"{prefix} {m['content']}")
