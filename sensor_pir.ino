/*
 * =====================================================================
 * ⚠️ DISABLED: MOTION SENSOR (PIR) ⚠️
 * 
 * As requested, this sensor is no longer used in the project. 
 * It was triggering constantly even when nothing was passing.
 * 
 * The camera is now triggered automatically by the Django server
 * whenever the ultrasonic sensor detects a 1% change in fill level.
 * 
 * DO NOT FLASH THIS FILE.
 * =====================================================================
 */
void setup() {
  Serial.begin(115200);
  Serial.println("PIR Sensor is DISABLED.");
}

void loop() {
  delay(1000);
}
