/*
 * Duraknot fence-roll line -- sensor node firmware
 * Board: ESP32 (Arduino Uno also works if ENABLE_WIFI is left undefined)
 *
 * Sense  -> rotary encoder / IR slotted-disc counter on the take-up spool
 *           (length + derived speed), analog vibration/tension sensor
 *           (weld & mesh-spacing defect events).
 * Stream -> one JSON object per second, either over USB serial (default,
 *           read by backend/serial_bridge.py) or over WiFi straight to the
 *           Flask backend's POST /api/ingest (set ENABLE_WIFI below).
 *
 * JSON shape, one line per second:
 *   {"length_m":123.45,"speed_mpm":12.30,"status":"RUNNING","defect":0,"defect_type":null}
 */

// ---- Uncomment to stream over WiFi instead of / in addition to serial ----
// #define ENABLE_WIFI

#ifdef ENABLE_WIFI
#include <WiFi.h>
#include <HTTPClient.h>
const char* WIFI_SSID     = "your-ssid";
const char* WIFI_PASSWORD = "your-password";
const char* INGEST_URL    = "http://192.168.1.50:5000/api/ingest"; // backend host:port
#endif

// ---------------- PIN MAP ----------------
const int ENCODER_PIN   = 4;   // interrupt-capable GPIO -- IR slotted-disc / rotary encoder
const int VIBRATION_PIN = 34;  // analog input -- vibration / tension sensor

// ---------------- CALIBRATION ----------------
// Re-calibrating for a different spool diameter is this one constant.
const float PULSES_PER_METRE = 40.0;     // encoder pulses per metre of fence roll
const int   DEFECT_THRESHOLD  = 2800;    // analog reading (0-4095) above which a tick is a defect
const float STOP_SPEED_EPS    = 0.15;    // m/min below which the line reads as STOPPED

// Bucket the vibration amplitude into the same defect categories the
// dashboard tracks, matching the case study's Pareto breakdown.
const char* defectTypeForReading(int analogVal) {
  if (analogVal > 3700) return "Weld quality";
  if (analogVal > 3300) return "Mesh spacing";
  if (analogVal > 3000) return "Coating uniformity";
  return "Wire tension";
}

// ---------------- STATE ----------------
volatile unsigned long pulseCount = 0;
unsigned long lastPulseCount = 0;
float totalLengthM = 0.0;
unsigned long lastTickMs = 0;

void IRAM_ATTR onEncoderPulse() {
  pulseCount++;
}

void setup() {
  Serial.begin(115200);
  pinMode(ENCODER_PIN, INPUT_PULLUP);
  pinMode(VIBRATION_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(ENCODER_PIN), onEncoderPulse, RISING);

#ifdef ENABLE_WIFI
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected, IP: ");
  Serial.println(WiFi.localIP());
#endif

  lastTickMs = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - lastTickMs < 1000) return;   // sample once per second
  lastTickMs = now;

  noInterrupts();
  unsigned long pulses = pulseCount;
  interrupts();

  unsigned long deltaPulses = pulses - lastPulseCount;
  lastPulseCount = pulses;

  float deltaLengthM = deltaPulses / PULSES_PER_METRE;
  totalLengthM += deltaLengthM;
  float speedMpm = deltaLengthM * 60.0;   // this tick's delta, extrapolated to a per-minute rate

  const char* status = (speedMpm > STOP_SPEED_EPS) ? "RUNNING" : "STOPPED";

  int vib = analogRead(VIBRATION_PIN);
  bool defect = (status[0] == 'R') && (vib > DEFECT_THRESHOLD);
  const char* defectType = defect ? defectTypeForReading(vib) : nullptr;

  String json = "{";
  json += "\"length_m\":" + String(totalLengthM, 2) + ",";
  json += "\"speed_mpm\":" + String(speedMpm, 2) + ",";
  json += "\"status\":\"" + String(status) + "\",";
  json += "\"defect\":" + String(defect ? 1 : 0) + ",";
  json += "\"defect_type\":" + (defect ? ("\"" + String(defectType) + "\"") : String("null"));
  json += "}";

  Serial.println(json);

#ifdef ENABLE_WIFI
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(INGEST_URL);
    http.addHeader("Content-Type", "application/json");
    http.POST(json);
    http.end();
  }
#endif
}
