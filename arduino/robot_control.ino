#include <SoftwareSerial.h>

SoftwareSerial BT(2,3);   // RX, TX

// ================= MOTOR PINS =================

#define IN1 8
#define IN2 9
#define IN3 10
#define IN4 11
#define BLADE 6 // grass cutting motor relay

#define RELAY 7

String currentDir = "E";
String cmd="";

// ================= SIGNALS =================

// ================= CALIBRATION =================
// 🔥 ADJUST THESE VALUES BASED ON YOUR ROBOT
#define FORWARD_TIME 1000     // time to move one cell (ms)
#define TURN_90_TIME 500      // time for 90 degree turn
#define TURN_180_TIME 1000    // time for 180 turn
#define STOP_DELAY 200        // stabilization delay

// ================= SIGNALS =================

void startSignal()
{
  digitalWrite(RELAY,HIGH);
  delay(200);
  digitalWrite(RELAY,LOW);
}

void endSignal()
{
  digitalWrite(RELAY,HIGH);
  delay(600);
  digitalWrite(RELAY,LOW);
}

void turnSignal()
{
  for(int i=0;i<3;i++)
  {
    digitalWrite(RELAY,HIGH);
    delay(250);
    digitalWrite(RELAY,LOW);
    delay(250);
  }
}

// ================= BLADE MOTOR =================

void bladeOn()
{
  digitalWrite(BLADE, HIGH);
  Serial.println("BLADE ON");
}

void bladeOff()
{
  digitalWrite(BLADE, LOW);
  Serial.println("BLADE OFF");
}


// ================= MOTOR =================

void stopMotor()
{
 digitalWrite(IN1,LOW);
 digitalWrite(IN2,LOW);
 digitalWrite(IN3,LOW);
 digitalWrite(IN4,LOW);
}

// ================= BASIC MOVEMENTS =================

void forward()
{
 digitalWrite(IN1,HIGH);
 digitalWrite(IN2,LOW);

 digitalWrite(IN3,HIGH);
 digitalWrite(IN4,LOW);
}

void backward()
{
 digitalWrite(IN1,LOW);
 digitalWrite(IN2,HIGH);

 digitalWrite(IN3,LOW);
 digitalWrite(IN4,HIGH);
}

void turnLeft()
{
 digitalWrite(IN1,LOW);
 digitalWrite(IN2,HIGH);

 digitalWrite(IN3,HIGH);
 digitalWrite(IN4,LOW);
}

void turnRight()
{
 digitalWrite(IN1,HIGH);
 digitalWrite(IN2,LOW);

 digitalWrite(IN3,LOW);
 digitalWrite(IN4,HIGH);
}

// ================= MOVEMENT FUNCTIONS =================

void moveForwardCell()
{
 startSignal();
  bladeOn();   // 🔥 START CUTTING
 forward();
 delay(FORWARD_TIME);   // adjust for your grid cell

 delay(STOP_DELAY);
 bladeOff();  // 🔥 STOP CUTTING
 endSignal();
//  Serial.println("TURNED");
}

void rotateLeft90()
{
 turnSignal();

 turnLeft();
//  delay(600);   // adjust for 90 degree turn
 delay(TURN_90_TIME);

 stopMotor();
 delay(STOP_DELAY);
}

void rotateRight90()
{
 turnSignal();

 turnRight();
//  delay(600);
  delay(TURN_90_TIME);

 stopMotor();
 delay(STOP_DELAY);
}

void rotate180()
{
 turnSignal();

 turnRight();
//  delay(1200);
 delay(TURN_180_TIME);

 stopMotor();
  delay(STOP_DELAY);
}

// ================= DIRECTION LOGIC =================

void moveTo(String target)
{

 Serial.print("Current: ");
 Serial.print(currentDir);
 Serial.print(" -> Target: ");
 Serial.println(target);

 if(currentDir == target)
 {
   moveForwardCell();
 }

 else if(
   (currentDir=="N" && target=="S") ||
   (currentDir=="S" && target=="N") ||
   (currentDir=="E" && target=="W") ||
   (currentDir=="W" && target=="E")
 )
 {
   rotate180();
   moveForwardCell();
  //  Serial.println("TURNED");
 }

 else if(
   (currentDir=="N" && target=="E") ||
   (currentDir=="E" && target=="S") ||
   (currentDir=="S" && target=="W") ||
   (currentDir=="W" && target=="N")
 )
 {
   rotateRight90();
   moveForwardCell();
  //  Serial.println("TURNED");
 }

 else
 {
   rotateLeft90();
   moveForwardCell();
  //  Serial.println("TURNED");
 }
 Serial.println("TURNED");

 currentDir = target;

    // send signal to Python
}

// ================= COMMAND PROCESS =================

void processCommand(String cmd)
{

 if(cmd=="N" || cmd=="S" || cmd=="E" || cmd=="W")
 {
   moveTo(cmd);
 }

 else if(cmd=="STOP")
 {
   stopMotor();
 }

 else if(cmd=="START")
 {
   startSignal();
 }
 // 🔥 OPTIONAL CONTROL FROM PYTHON
  else if(cmd=="BLADE_ON")
  {
    bladeOn();
  }

  else if(cmd=="BLADE_OFF")
  {
    bladeOff();
  }

}

// ================= SETUP =================

void setup()
{
 Serial.begin(115200);
 BT.begin(9600);

 pinMode(IN1,OUTPUT);
 pinMode(IN2,OUTPUT);
 pinMode(IN3,OUTPUT);
 pinMode(IN4,OUTPUT);

 pinMode(RELAY,OUTPUT);

 stopMotor();

 Serial.println("Robot Ready");
}

// ================= LOOP =================

void loop()
{

 if(BT.available())
 {
   cmd = BT.readStringUntil('\n');
   cmd.trim();

   processCommand(cmd);
 }

 if(Serial.available())
 {
   cmd = Serial.readStringUntil('\n');
   cmd.trim();

   processCommand(cmd);
 }

}
