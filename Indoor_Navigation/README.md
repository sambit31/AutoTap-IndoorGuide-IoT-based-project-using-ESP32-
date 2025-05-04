# 🌐 ESP32 Mesh Network | Indoor Navigation for the Visually Impaired

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![ESP32](https://img.shields.io/badge/device-ESP32-red.svg)

> **Navigate spaces, not obstacles.** A wireless mesh network solution that brings GPS-like navigation indoors for the visually impaired - no internet required.

## ✨ Features

- **Self-healing mesh network** using ESP32 microcontrollers
- **Real-time position tracking** without GPS or WiFi infrastructure
- **Voice-first interface** for hands-free navigation assistance
- **Low-cost, easily deployable** nodes for any indoor environment
- **Python visualization** with intuitive GUI for monitoring
- **Smart device control** integration (water pump, lights, etc.)
- **Open-source** and extensible for custom environments

## 🧠 How It Works

The system creates a wireless mesh network where:

1. **Multiple ESP32 nodes** establish a resilient mesh network
2. A **wearable node** (carried by user) broadcasts its presence
3. **Fixed nodes** measure signal strength (RSSI) from the wearable
4. A **root node** collects all data and sends to computer via USB
5. **Trilateration algorithm** with Kalman filtering calculates precise position
6. **Real-time visualization** shows user's location on indoor map
7. **Voice assistant** uses Gemini AI to provide verbal navigation instructions

### Voice Assistant Features:
- Hands-free voice command recognition
- AI-powered contextual navigation guidance
- Text-to-speech feedback for visually impaired users

![Mesh Network Concept](https://via.placeholder.com/800x400?text=Mesh+Network+Concept)

## 🛠️ Hardware Requirements

- **3+ ESP32 Development Boards**
  - 1× Root Node (connected to computer)
  - 1× Wearable Node (carried by user)
  - 1+ Fixed Nodes (distributed in environment)
- **Power Supply Options**
  - LiPo battery for wearable node

## 💻 Software Requirements

### ESP32 Development
- Arduino IDE with ESP32 board support
- Libraries:
  - painlessMesh
  - WiFi
  - ArduinoJson

### Position Visualization
- Python 3.x with:
  - matplotlib
  - numpy
  - tkinter
  - pyserial

### Voice Assistant
- Python 3.x with:
  - streamlit
  - google.generativeai (Gemini API)
  - SpeechRecognition
  - pyttsx3 (Text-to-Speech)
  - python-dotenv

## 📂 Repository Structure

```
MeshNetwork/
│
├── node.ino             # Universal ESP32 node firmware
├── gui.py               # Python visualization interface
├── voice_assistant.py   # Voice-based navigation & control interface
├── README.md            # Project documentation
└── diagrams/            # System architecture diagrams
```

## 🚀 Getting Started

### 1. Setting Up ESP32 Nodes

```bash
# Clone this repository
git clone https://github.com/sambit31/AutoTap-IndoorGuide-IoT-based-project-using-ESP32-.git
cd AutoTap-IndoorGuide/MeshNetwork

# Open Arduino IDE
# Load node.ino
# Select ESP32 board
# Upload to all ESP32 boards
```

### 2. Node Placement

- Place fixed nodes around your indoor space
- Ensure overlapping coverage for reliable positioning
- Connect the root node to your computer via USB

### 3. Running the Visualization

```bash
# Install Python dependencies
pip install matplotlib numpy pyserial

# Run the visualization
python gui.py
```

### 4. Setting Up Voice Assistant

```bash
# Install voice assistant dependencies
pip install streamlit google-generativeai SpeechRecognition pyttsx3 python-dotenv

# Create .env file with your API keys
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
echo "ESP32_IP=192.168.63.12" >> .env

# Run the voice assistant
streamlit run voice_assistant.py
```

## 📊 System Performance

- **Typical Accuracy:** 1-2 meters (depending on node density)
- **Update Rate:** ~2 Hz (configurable)
- **Maximum Coverage:** ~400 sq. meters (with 8 nodes)
- **Battery Life:** 8-12 hours for wearable node

## 🔮 Future Enhancements

- [ ] Ultrasonic sensor integration for obstacle detection
- [ ] Mobile app connectivity via Bluetooth
- [x] Voice guidance capabilities
- [ ] Expanded voice command vocabulary
- [ ] Multi-language support for voice interface
- [ ] Cloud data logging for movement analysis
- [ ] Machine learning for improved accuracy

## 🤝 Contributing

We welcome contributions to improve this system! Whether it's feature enhancements, bug fixes, or documentation improvements.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- This system is part of the "AutoTap-IndoorGuide" IoT project
- Built to support the visually impaired through smart automation and offline tracking
- Inspired by the need for affordable, infrastructure-independent navigation solutions

---

<p align="center">
  <b>Made with ❤️ for accessibility</b>
</p>