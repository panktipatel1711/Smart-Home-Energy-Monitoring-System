#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100";
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "home/energy/node1/telemetry";

const int ADC_INPUT_PIN    = 34;
const int SAFETY_RELAY_PIN = 25;
const int ALERT_BUZZER_PIN = 26;

const float INTERN_VREF       = 3.3;
const float TOTAL_ADC_STEPS   = 4095.0;
const float NOMINAL_VOLTAGE   = 230.0;
const float AMPS_PER_VOLT     = 50.0;
const float OVERCURRENT_LIMIT = 15.0;

unsigned long lastTelemetryTimestamp = 0;
double cumulativeWattHours = 0.0;
WiFiClient espWiFiClient;
PubSubClient mqttClient(espWiFiClient);

void initializeWiFi() {
    delay(10);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
}

void enforceMQTTConnection() {
    while (!mqttClient.connected()) {
        if (mqttClient.connect("ESP32EnergyMonitorNode")) break;
        delay(5000);
    }
}

float calculateTrueRootMeanSquareCurrent() {
    long sampleSum = 0;
    int sampledPointsCount = 0;
    unsigned long samplingWindowStart = millis();
    while ((millis() - samplingWindowStart) < 400) {
        int rawAnalogSample = analogRead(ADC_INPUT_PIN);
        int normalizedSample = rawAnalogSample - 2048;
        sampleSum += (normalizedSample * normalizedSample);
        sampledPointsCount++;
        delayMicroseconds(250);
    }
    return (sqrt((float)sampleSum / (float)sampledPointsCount) / TOTAL_ADC_STEPS) * INTERN_VREF * AMPS_PER_VOLT;
}

void setup() {
    Serial.begin(115200);
    pinMode(SAFETY_RELAY_PIN, OUTPUT);
    pinMode(ALERT_BUZZER_PIN, OUTPUT);
    digitalWrite(SAFETY_RELAY_PIN, HIGH);
    analogReadResolution(12);
    initializeWiFi();
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
}

void loop() {
    if (!mqttClient.connected()) enforceMQTTConnection();
    mqttClient.loop();
    unsigned long currentMillis = millis();
    if (currentMillis - lastTelemetryTimestamp >= 1000) {
        float rootMeanSquareCurrent = calculateTrueRootMeanSquareCurrent();
        if (rootMeanSquareCurrent < 0.08) rootMeanSquareCurrent = 0.0;
        float calculatedApparentPower = NOMINAL_VOLTAGE * rootMeanSquareCurrent;
        cumulativeWattHours += (calculatedApparentPower * (1.0 / 3600.0));
        bool overloadFlag = (rootMeanSquareCurrent >= OVERCURRENT_LIMIT);
        if (overloadFlag) { digitalWrite(SAFETY_RELAY_PIN, LOW); digitalWrite(ALERT_BUZZER_PIN, HIGH); }
        else { digitalWrite(ALERT_BUZZER_PIN, LOW); }
        
        char payload[256];
        snprintf(payload, sizeof(payload), "{\"voltage\":%.1f,\"current\":%.3f,\"power\":%.1f,\"energy_wh\":%.3f,\"overload\":%s}",
                 NOMINAL_VOLTAGE, rootMeanSquareCurrent, calculatedApparentPower, cumulativeWattHours, overloadFlag ? "true" : "false");
        Serial.println(payload);
        mqttClient.publish(MQTT_TOPIC, payload);
        lastTelemetryTimestamp = currentMillis;
    }
}
