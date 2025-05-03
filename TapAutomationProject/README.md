
# 🚰 AutoTap System – Smart Touchless Water Control

## 🔍 Overview

AutoTap is a smart, touchless water control system designed for **visually impaired individuals** and general hands-free hygiene use. It utilizes **dual input modes** — **IR sensor-based hand detection** and **voice command via Gemini AI (Python)** — to control a 5V water pump using an ESP32 microcontroller. This system offers safety, automation, and accessibility in daily water usage environments such as kitchens, bathrooms, or public restrooms.

---

## 🎯 Key Features

- ✋ **IR Sensor Activation** – Detects hand presence to trigger water flow
- 🎙️ **Voice Command Control** – Voice-based tap control using Gemini and Python
- 📶 **Wi-Fi Based Communication** – ESP32 receives voice control commands wirelessly
- 🔌 **Low Power Efficient** – Uses buck converter and relay for safe operation
- 👁️‍🗨️ **Designed for Visually Impaired** – Enables hands-free interaction
- 🔄 **Dual Mode Operation** – Works even if one input mode fails

---

## 📐 System Architecture

```plaintext
            [Hand]
              ↓
         +------------+          Voice Command
         |  IR Sensor |          (Python + Gemini)
         +------------+                   ↓
              ↓                          [Wi-Fi]
         +---------------------------+    ↓
         |         ESP32            |<----+
         |  • Reads IR input        |
         |  • Receives Wi-Fi cmd    |
         |  • Controls Relay Module |
         +---------------------------+
                         ↓
                  +------------+
                  | Relay + Pump|
                  +------------+
                         ↓
                 [Water Pipeline]
```

---

## 🔩 Components Used

| Component | Quantity | Description |
|-----------|----------|-------------|
| ESP32 | 1 | Main microcontroller with Wi-Fi |
| IR Sensor (Hand Detection) | 1 | Detects presence of hand |
| 5V DC Water Pump | 1 | Used to control water flow |
| Relay Module (5V) | 1 | Controls high power pump |
| LM2596 Buck Converter | 1 | Steps down voltage for ESP32 |
| I2C Logic Level Converter | 1 | For safe voltage interfacing |
| Breadboard + Jump Wires | 1 | For circuit connections |
| 2 x 18650 Batteries / 9V | 1–2 | Power supply |
| Water Pipe | 1 | For connecting pump to outlet |
| Python (voice_assistant.py) | 1 | Sends voice commands over Wi-Fi |
| Gemini API | – | AI model for voice understanding |

---

## ⚡ Circuit Connections

➤ **IR Sensor to ESP32:**
- VCC → 3.3V
- GND → GND
- OUT → GPIO 4

➤ **Relay Module:**
- IN → GPIO 5
- VCC → VIN (from buck converter)
- GND → GND
- Pump V+ → Relay NO
- Pump V– → Ground

➤ **Buck Converter:**
- Input → 2 Batteries (7.4V)
- Output → 5V (To ESP32 VIN and Relay)

➤ **Python Voice Assistant:**
- Python script uses Gemini to interpret voice
- Sends HTTP requests to ESP32 to toggle pump
- ESP32 runs server that listens for /on or /off

---

## 🚀 How It Works

- Hand Detected by IR Sensor → ESP32 turns pump ON.
- Voice Command "Turn on tap" → Gemini interprets → Python sends signal → ESP32 activates relay → Water flows.

ESP32 runs combined logic:

```cpp
if (digitalRead(IR_PIN) == HIGH || voiceCommand == "on") {
    digitalWrite(RELAY_PIN, HIGH);
} else if (voiceCommand == "off") {
    digitalWrite(RELAY_PIN, LOW);
}
```

---

## 🧪 Usage Instructions

1. Connect all components as per circuit above.
2. Upload main.ino to ESP32 using Arduino IDE.
3. Run voice_assistant.py on your PC with internet.
4. Speak voice commands: "Turn on tap", "Stop water", etc.
5. Place hand in front of IR sensor to test automatic activation.

---

## 🧱 Project Modules

- main.ino – C++ code on ESP32 for IR + relay control
- voice_assistant.py – Voice interface (Gemini + Python)
- .env – Contains Gemini and Wi-Fi credentials

---

## 🧠 Real-Life Applications

- Visually impaired-friendly bathrooms
- Touchless faucets in public spaces
- Kitchen taps for hygiene
- Smart home water control systems

---

## ❗ Limitations

- Requires stable Wi-Fi for voice commands
- Voice assistant runs separately on a computer or Raspberry Pi
- Gemini API usage may have limits depending on plan

---

## 🔮 Future Improvements

- Integrate voice module directly into ESP32
- Add water usage monitoring via flow sensor
- Mobile app for remote monitoring and analytics

---


