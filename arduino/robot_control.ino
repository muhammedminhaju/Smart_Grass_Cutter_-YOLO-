#include <SoftwareSerial.h>

SoftwareSerial BT(2,3);   // RX, TX

// ================= MOTOR PINS =================
#define IN1 8
#define IN2 9
#define IN3 10
#define IN4 11 

#define RELAY 7

String currentDir = "E";
String cmd="";

// ================= CALIBRATION =================
// 🔥 ADJUST THESE VALUES BASED ON YOUR ROBOT
#define FORWARD_TIME 3000     // time to move one cell (ms)
#define TURN_90_TIME 500      // time for 90 degree turn
#define TURN_180_TIME 1000    // time for 180 turn
#define STOP_DELAY 200        // stabilization delay
// ================= SIGNALS =================

void startSignal()
{
  digitalWrite(RELAY,HIGH);
  delay(500);
  digitalWrite(RELAY,LOW);
}

void endSignal()
{
  digitalWrite(RELAY,HIGH);
  delay(1500);
  digitalWrite(RELAY,LOW);
}

void turnSignal()
{
  for(int i=0;i<3;i++)
  {
    digitalWrite(RELAY,HIGH);
    delay(300);
    digitalWrite(RELAY,LOW);
    delay(300);
  }
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

// ================= MOVEMENT =================

void moveForwardCell()
{
 startSignal();

 forward();
 delay(FORWARD_TIME);

 stopMotor();
 delay(300);

 endSignal();
}

// 🔥🔥🔥 MAXIMUM DELAY VALUES
int turnDelay = 1200;     // 90° (very high)
int turnDelay180 = 2400;  // 180° (guaranteed full turn)

// ================= TURN FUNCTIONS =================

void rotateLeft90()
{
 turnSignal();

 turnLeft();
 delay(turnDelay);

 stopMotor();
 delay(400);
}

void rotateRight90()
{
 turnSignal();

 turnRight();
 delay(turnDelay);

 stopMotor();
 delay(400);
}

// 🔥 STRONG 180° TURN (single long rotation)
void rotate180()
{
 turnSignal();

 turnRight();
 delay(turnDelay180);

 stopMotor();
 delay(500);
}

// ================= DIRECTION LOGIC =================

void moveTo(String target)
{
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
 }

 else
 {
   rotateLeft90();
   moveForwardCell();
 }

 currentDir = target;
}

// ================= COMMAND =================

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