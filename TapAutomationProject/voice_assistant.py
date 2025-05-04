import streamlit as st
import speech_recognition as sr
import requests
import time
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# ESP32 Web Server URL
ESP32_URL = "http://192.168.64.12"  # Replace with your ESP32's IP address

def classify_intent(text):
    prompt = f"""
    Classify the following user input into one of these categories:
    1. pump_on - User wants to turn the pump/tap on
    2. pump_off - User wants to turn the pump/tap off
    3. general - General conversation or other commands

    Input: "{text}"
    Respond with ONLY the category name.
    """
    
    response = model.generate_content(prompt)
    return response.text.strip().lower()

def control_pump(action):
    try:
        if action == "pump_on":
            requests.get(f"{ESP32_URL}/on")
            return "Pump turned ON"
        elif action == "pump_off":
            requests.get(f"{ESP32_URL}/off")
            return "Pump turned OFF"
    except Exception as e:
        return f"Error: {str(e)}"

def listen_to_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Error with speech recognition: {str(e)}"

def main():
    st.title("Voice-Controlled Pump Assistant")
    
    if st.button("Start Listening"):
        user_input = listen_to_speech()
        st.write(f"You said: {user_input}")
        
        if user_input and not user_input.startswith("Could not"):
            intent = classify_intent(user_input)
            st.write(f"Intent: {intent}")
            
            if intent in ["pump_on", "pump_off"]:
                result = control_pump(intent)
                st.write(result)
            else:
                st.write("I understood your message but it wasn't a pump control command.")

if __name__ == "__main__":
    main() 