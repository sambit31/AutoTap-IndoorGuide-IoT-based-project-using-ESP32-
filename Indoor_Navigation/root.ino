#include <painlessMesh.h>
#include <WiFi.h>
#include "esp_wifi.h"  // Required for promiscuous mode

#define MESH_PREFIX     "ESP32Mesh"
#define MESH_PASSWORD   "meshpassword"
#define MESH_PORT       5555

Scheduler userScheduler;
painlessMesh mesh;

// ====== Function Prototypes ======
void sendPing();
void sendRSSIReport();
void checkRootStatus();
void receivedCallback(uint32_t from, String &msg);
void newConnectionCallback(uint32_t nodeId);
void changedConnectionCallback();
uint32_t getRootNodeId();
void promiscuousRxCb(void *buf, wifi_promiscuous_pkt_type_t type);

// ====== Task Definitions ======
Task taskSendPing(TASK_SECOND * 2, TASK_FOREVER, &sendPing);
Task taskSendRSSIReport(TASK_SECOND * 5, TASK_FOREVER, &sendRSSIReport);
Task taskCheckRoot(TASK_SECOND * 3, TASK_FOREVER, &checkRootStatus);

// ====== Global Variables ======
uint32_t nodeId;
bool isRoot = false;
std::vector<uint32_t> connectedNodes;  // List of NodeIDs

// Measured live RSSI values
std::map<uint32_t, int32_t> peerRSSI;

// ====== Setup ======
void setup() {
  Serial.begin(115200);

  // Print MAC and NodeID for setup
  WiFi.mode(WIFI_AP_STA);
  Serial.printf("[BOOT] NodeID: %u, MAC: %s\n", mesh.getNodeId(), WiFi.macAddress().c_str());

  // Mesh init
  mesh.setDebugMsgTypes(ERROR | STARTUP);  
  mesh.init(MESH_PREFIX, MESH_PASSWORD, MESH_PORT, WIFI_AP_STA, 6);

  nodeId = mesh.getNodeId();

  mesh.onReceive(&receivedCallback);
  mesh.onNewConnection(&newConnectionCallback);
  mesh.onChangedConnections(&changedConnectionCallback);

  userScheduler.addTask(taskSendPing);
  taskSendPing.enable();

  userScheduler.addTask(taskSendRSSIReport);
  taskSendRSSIReport.enable();

  userScheduler.addTask(taskCheckRoot);
  taskCheckRoot.enable();

  // Enable Promiscuous mode for sniffing
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_promiscuous_rx_cb(&promiscuousRxCb);
}

// ====== Loop ======
void loop() {
  mesh.update();
  userScheduler.execute();
}

// ====== Tasks Implementation ======

void sendPing() {
  String msg = "PING," + String(nodeId);
  mesh.sendBroadcast(msg);
}

void sendRSSIReport() {
  if (isRoot) return;  // Root doesn't report

  if (peerRSSI.empty()) return;

  String report = "RSSI," + String(nodeId);
  for (auto &entry : peerRSSI) {
    report += "," + String(entry.first) + ":" + String(entry.second);
  }

  mesh.sendSingle(getRootNodeId(), report);
  peerRSSI.clear();  // Reset after sending
}

void checkRootStatus() {
  uint32_t currentRoot = getRootNodeId();
  bool wasRoot = isRoot;
  isRoot = (nodeId == currentRoot);

  if (isRoot && !wasRoot) {
    Serial.printf("[NODE %u] Elected as ROOT\n", nodeId);
  } else if (!isRoot && wasRoot) {
    Serial.printf("[NODE %u] No longer ROOT, now client\n", nodeId);
  }
}

// ====== Mesh Callbacks ======

void receivedCallback(uint32_t from, String &msg) {
  if (msg.startsWith("PING")) {
    Serial.printf("[NODE %u] Heard PING from %u\n", nodeId, from);
    
    // Root node processes PINGs differently, if needed
    if (isRoot) {
      Serial.printf("[ROOT] Handling PING from %u\n", from);
    }
  } else if (isRoot) {
    // Root node processes RSSI report messages
    if (msg.startsWith("RSSI")) {
      Serial.printf("[ROOT] Received RSSI report: %s\n", msg.c_str());
      // Process RSSI data here, possibly log it or take action based on RSSI values
    }
  }
}

void newConnectionCallback(uint32_t nodeId) {
  Serial.printf("[NODE %u] New connection: %u\n", mesh.getNodeId(), nodeId);
}

void changedConnectionCallback() {
  connectedNodes.clear();
  auto nodes = mesh.getNodeList();
  for (auto id : nodes) {
    connectedNodes.push_back(id);
  }
  connectedNodes.push_back(nodeId);  // Include self
}

uint32_t getRootNodeId() {
  uint32_t minId = nodeId;
  for (auto id : connectedNodes) {
    if (id < minId) {
      minId = id;
    }
  }
  return minId;
}

// ====== Promiscuous Sniffer ======

void promiscuousRxCb(void *buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_MGMT) return;  // Only Management frames (beacons, probe, etc.)

  wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t *)buf;
  int rssi = pkt->rx_ctrl.rssi;
  uint8_t *addr = pkt->payload + 10; // sender MAC address
  char macStr[18];
  sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", 
    addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]);
  String mac(macStr);

  // Process RSSI if MAC is known
  // For the root node, you might log the RSSI or analyze the signal strength.
  Serial.printf("[ROOT] RSSI from MAC %s: %d\n", mac.c_str(), rssi);
}