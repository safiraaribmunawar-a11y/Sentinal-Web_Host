#include <Key.h>
#include <Keypad.h>

/*
 * EDR Arduino Controller
 * ========================
 * Hardware:
 *   - Green LED   -> Pin 9
 *   - Yellow LED  -> Pin 10
 *   - Red LED     -> Pin 11
 *   - Buzzer      -> Pin 6  (piezo, active or passive)
 *   - Kill Switch -> Pin 2 (toggle switch, INPUT_PULLUP)
 *   - 4x4 Keypad  -> Pins 3,4,5,7 (rows) + A0,A1,A2,A3 (cols)
 *
 * Buzzer behavior:
 *   - WARN start  -> single beep only
 *   - During 20s  -> silent (yellow LED blinks)
 *   - After timeout (RED) -> continuous two-tone siren until kill switch
 *   - Kill switch -> stops buzzer immediately, resets to green
 *
 * Serial Protocol (9600 baud):
 *   PC -> Arduino:
 *     LED:GREEN\n      -> green on, others off
 *     LED:YELLOW\n     -> yellow on, others off
 *     LED:RED\n        -> red on, others off
 *     WARN:20\n        -> start 20s warning countdown
 *     CANCEL\n         -> cancel warning, go back to yellow
 *   Arduino -> PC:
 *     KILL:1\n         -> kill switch activated
 *     KILL:0\n         -> kill switch deactivated
 *     CODE:xxxx\n      -> keypad code submitted
 */

#include <Keypad.h>

// Pin Definitions
const int PIN_LED_GREEN  = 9;
const int PIN_LED_YELLOW = 10;
const int PIN_LED_RED    = 11;
const int PIN_BUZZER     = 6;
const int PIN_KILL       = 2;

// Keypad Setup
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {3, 4, 5, 7};
byte colPins[COLS] = {A0, A1, A2, A3};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// State
enum LEDState { STATE_GREEN, STATE_YELLOW, STATE_RED, STATE_WARNING };
LEDState currentState = STATE_GREEN;

bool warningActive     = false;
bool severeAlarmActive = false;
unsigned long warningStart    = 0;
unsigned long warningDuration = 20000;

String inputCode      = "";
int    killSwitchLast = HIGH;
String serialBuffer   = "";

// Setup
void setup() {
  Serial.begin(9600);
  pinMode(PIN_LED_GREEN,  OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED,    OUTPUT);
  pinMode(PIN_BUZZER,     OUTPUT);
  pinMode(PIN_KILL,       INPUT_PULLUP);
  setLED(STATE_GREEN);
  delay(500);
  Serial.println("EDR:READY");
}

// Main Loop
void loop() {
  readSerial();
  readKillSwitch();
  readKeypad();
  runWarningCountdown();
  runSevereAlarm();
}

// Serial Input
void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      handleCommand(serialBuffer);
      serialBuffer = "";
    } else if (c != '\r') {
      serialBuffer += c;
    }
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd == "LED:GREEN") {
    cancelWarning();
    severeAlarmActive = false;
    setLED(STATE_GREEN);
  }
  else if (cmd == "LED:YELLOW") {
    cancelWarning();
    severeAlarmActive = false;
    setLED(STATE_YELLOW);
  }
  else if (cmd == "LED:RED") {
    cancelWarning();
    setLED(STATE_RED);
    severeAlarmActive = true;
  }
  else if (cmd.startsWith("WARN:")) {
    int seconds = cmd.substring(5).toInt();
    startWarning(seconds);
  }
  else if (cmd == "CANCEL") {
    cancelWarning();
    severeAlarmActive = false;
    setLED(STATE_YELLOW);
  }
}

// LED Control
void setLED(LEDState state) {
  currentState = state;
  digitalWrite(PIN_LED_GREEN,  state == STATE_GREEN  ? HIGH : LOW);
  digitalWrite(PIN_LED_YELLOW, state == STATE_YELLOW ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,    state == STATE_RED    ? HIGH : LOW);
  noTone(PIN_BUZZER);
}

void allLEDsOff() {
  digitalWrite(PIN_LED_GREEN,  LOW);
  digitalWrite(PIN_LED_YELLOW, LOW);
  digitalWrite(PIN_LED_RED,    LOW);
}

// Warning Countdown — one beep at start, silent during countdown
void startWarning(int seconds) {
  warningDuration   = (unsigned long)seconds * 1000;
  warningStart      = millis();
  warningActive     = true;
  severeAlarmActive = false;
  inputCode         = "";
  currentState      = STATE_WARNING;
  // Single beep at start
  tone(PIN_BUZZER, 1200, 300);
}

void cancelWarning() {
  warningActive = false;
  noTone(PIN_BUZZER);
}

void runWarningCountdown() {
  if (!warningActive) return;
  unsigned long elapsed = millis() - warningStart;

  // Blink yellow LED — no buzzer during countdown
  bool blink = (millis() / 250) % 2 == 0;
  digitalWrite(PIN_LED_YELLOW, blink ? HIGH : LOW);
  digitalWrite(PIN_LED_GREEN,  LOW);
  digitalWrite(PIN_LED_RED,    LOW);

  // Timeout -> red LED + start continuous alarm
  if (elapsed >= warningDuration) {
    warningActive = false;
    allLEDsOff();
    digitalWrite(PIN_LED_RED, HIGH);
    currentState      = STATE_RED;
    severeAlarmActive = true;
  }
}

// Continuous two-tone siren after SEVERE — runs until kill switch
void runSevereAlarm() {
  if (!severeAlarmActive) return;
  // Alternates between 880Hz and 1100Hz every 500ms
  unsigned long t = millis() / 500;
  if (t % 2 == 0) {
    tone(PIN_BUZZER, 880);
  } else {
    tone(PIN_BUZZER, 1100);
  }
}

// Kill Switch
void readKillSwitch() {
  int killState = digitalRead(PIN_KILL);
  if (killState != killSwitchLast) {
    killSwitchLast = killState;
    delay(50); // debounce
    if (killState == LOW) {
      Serial.println("KILL:1");
      cancelWarning();
      severeAlarmActive = false;  // stops continuous buzz
      noTone(PIN_BUZZER);
      setLED(STATE_GREEN);
      // Two quick confirmation beeps
      tone(PIN_BUZZER, 1200, 100);
      delay(150);
      tone(PIN_BUZZER, 1400, 100);
    } else {
      Serial.println("KILL:0");
    }
  }
}

// Keypad Input
void readKeypad() {
  char key = keypad.getKey();
  if (!key) return;
  if (key == '#') {
    if (inputCode.length() > 0) {
      Serial.print("CODE:");
      Serial.println(inputCode);
      inputCode = "";
      tone(PIN_BUZZER, 1600, 80);
    }
  }
  else if (key == '*') {
    inputCode = "";
    tone(PIN_BUZZER, 400, 80);
  }
  else if (key >= '0' && key <= '9') {
    if (inputCode.length() < 8) {
      inputCode += key;
      tone(PIN_BUZZER, 1200, 50);
    }
  }
}
