const int PIN_SAFE = 8;
const int PIN_ELEVATED = 9;
const int PIN_SEVERE = 10;
const int PIN_BUZZER = 11;
const int PIN_KILL = 7;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_SAFE, OUTPUT);
  pinMode(PIN_ELEVATED, OUTPUT);
  pinMode(PIN_SEVERE, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_KILL, INPUT_PULLUP);
  
  digitalWrite(PIN_SAFE, HIGH); delay(500); digitalWrite(PIN_SAFE, LOW);
}

void loop() {
  if (digitalRead(PIN_KILL) == LOW) {
    updateHardware("SAFE");
    return;
  }

  if (Serial.available() > 0) {
    String status = Serial.readStringUntil('\n');
    status.trim();
    updateHardware(status);
  }
}

void updateHardware(String status) {
  digitalWrite(PIN_SAFE, LOW);
  digitalWrite(PIN_ELEVATED, LOW);
  digitalWrite(PIN_SEVERE, LOW);
  noTone(PIN_BUZZER);

  if (status == "SAFE") digitalWrite(PIN_SAFE, HIGH);
  else if (status == "ELEVATED") digitalWrite(PIN_ELEVATED, HIGH);
  else if (status == "SEVERE") {
    digitalWrite(PIN_SEVERE, HIGH);
    tone(PIN_BUZZER, 1000);
  }
}