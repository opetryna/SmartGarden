void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  for (int i = 0; i < 6; i++) {
    int val = analogRead(i);
    Serial.print(val);
    Serial.print("\t");
  }
  Serial.println();
  delay(1000);
}
