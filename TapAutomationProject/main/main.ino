#include <WiFi.h>
#include <WebServer.h>

#define IR_SENSOR_PIN 13  // your IR sensor input
#define RELAY_PIN      5   // your relay control (active LOW)

const char* ssid     = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

WebServer server(80);

// Override control variables
bool webOverride = false;
unsigned long lastWebOnMillis = 0;
const unsigned long overrideDuration = 9000; // 3 seconds

// Simple HTML page with two buttons
const char htmlPage[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>ESP32 Pump Control</title>
    <style>
      body { font-family: Arial; text-align: center; margin-top: 50px; }
      button {
        padding: 20px 40px;
        font-size: 1.5em;
        margin: 20px;
        border: none;
        border-radius: 10px;
        cursor: pointer;
      }
      #on  { background: #4CAF50; color: #fff; }
      #off { background: #f44336; color: #fff; }
    </style>
  </head>
  <body>
    <h1>ESP32 Pump Control</h1>
    <button id="on"  onclick="fetch('/on')">Turn ON</button>
    <button id="off" onclick="fetch('/off')">Turn OFF</button>
    <p id="status">—</p>
    <script>
      // Poll status every second
      setInterval(() => {
        fetch('/status').then(r => r.text()).then(txt => {
          document.getElementById('status').innerText = 'Pump is ' + txt;
        });
      }, 1000);
    </script>
  </body>
</html>
)rawliteral";

void handleRoot() {
  server.send_P(200, "text/html", htmlPage);
}

void handlePumpOn() {
  digitalWrite(RELAY_PIN, LOW);     // active LOW
  webOverride = true;               // enable override
  lastWebOnMillis = millis();      // start timer
  server.sendHeader("Location", "/");
  server.send(303);
}

void handlePumpOff() {
  digitalWrite(RELAY_PIN, HIGH);    // turn OFF immediately
  webOverride = false;              // cancel override
  server.sendHeader("Location", "/");
  server.send(303);
}

void handleStatus() {
  bool isOn = (digitalRead(RELAY_PIN) == LOW);
  server.send(200, "text/plain", isOn ? "ON" : "OFF");
}

void setup() {
  Serial.begin(115200);
  pinMode(IR_SENSOR_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);    // start OFF

  // Connect to WiFi
  Serial.printf("Connecting to %s ...\n", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nConnected! IP address: %s\n", WiFi.localIP().toString().c_str());

  // Set up web server routes
  server.on("/",       HTTP_GET,  handleRoot);
  server.on("/on",     HTTP_GET,  handlePumpOn);
  server.on("/off",    HTTP_GET,  handlePumpOff);
  server.on("/status", HTTP_GET,  handleStatus);
  server.begin();
}

void loop() {
  server.handleClient();

  // If web override is active, keep pump ON for the overrideDuration
  if (webOverride) {
    if (millis() - lastWebOnMillis < overrideDuration) {
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("Web override active: Pump ON");
    } else {
      webOverride = false; // override expired
    }
  }

  // Only apply IR sensor logic when not under web override
  if (!webOverride) {
    int irState = digitalRead(IR_SENSOR_PIN);
    if (irState == LOW) {
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("IR: object detected → Pump ON");
    } else {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("IR: no object → Pump OFF");
    }
  }

  delay(200);
}
