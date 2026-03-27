import cv2
import numpy as np
import torch
import time
from ultralytics import YOLO
from collections import deque
import sys
import os
import serial
from datetime import datetime
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# FRAME SKIP (FPS BOOST)

frame_skip = 6
frame_counter = 0
global robot_dir_no,waiting_for_turn 
robot_dir_no = 0
waiting_for_turn = False

# PATH HANDLER

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)



# ARDUINO NANO SERIAL CONNECTION



try:
    nano = serial.Serial("COM3", 115200, timeout=1)  # Change COM if needed
    time.sleep(2)
    print("✅ Connected to Arduino Nano")
except Exception as e:
    nano = None
    print("⚠ Arduino not connected")
    print("ERROR:", e)
def send_direction(direction):
    global robot_dir_no,waiting_for_turn
    
    if nano and nano.is_open:
        try:
            nano.write((direction + '\n').encode())
            if direction in ["N", "E", "S", "W"]:
                robot_dir_no += 1
                waiting_for_turn = True
                print('Sent:',robot_dir_no,direction)
            else:
                print('Sent:',direction)  
        except:
             pass
    else:
        if direction in ["N", "E", "S", "W"]:
                robot_dir_no += 1
                waiting_for_turn = True
                print('Sent:',robot_dir_no,direction)
        else:
                print('Sent:',direction)    
def read_nano_signal():
    global machine_on,waiting_for_turn 
    
    if nano and nano.in_waiting > 0:
        try:
            msg = nano.readline().decode().strip()
            print("Nano:", msg)
      
            if msg == "TOGGLE":
                toggle_machine()

            elif msg == "STOP":
                machine_on = False
                send_direction("STOP")

            elif msg == "START":
                machine_on = True
            elif msg == "TURNED":
                waiting_for_turn = False 

                print("Turn completed","message:",msg)

        except:
            pass

# CUDA CHECK

print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
else:
    print("Running on CPU")

FLOOR_WIDTH_M = float(input("Enter floor width in meters (e.g. 2): "))
FLOOR_HEIGHT_M = float(input("Enter floor height in meters (e.g. 2): "))
MACHINE_WIDTH_M = 0.2
SPEED_MPS = 0.55 #33m/m

CELL_SIZE_M = MACHINE_WIDTH_M
GRID_SIZE_X = int(FLOOR_WIDTH_M / CELL_SIZE_M)
GRID_SIZE_Y = int(FLOOR_HEIGHT_M / CELL_SIZE_M)

CELL_SIZE = 60
MOVE_DELAY = CELL_SIZE_M / SPEED_MPS

print("Grid:", GRID_SIZE_X, "x", GRID_SIZE_Y)


# GRID 
grid = np.zeros((GRID_SIZE_Y, GRID_SIZE_X))

robot_x = 0
robot_y = 0
robot_dir = "E"

blade_on = False
emergency_stop = False
machine_on = False
coverage_complete = False
# obstacle_cooldown = 0
current_path = []

ANIMAL_CLASSES = ["person", "dog", "cat", "cow", "horse"]
OBSTACLE_CLASSES = ["chair", "bench", "bottle", "potted plant"]


# YOLO MODELS

model = YOLO("yolov8n.pt")
modelGrass = YOLO("Grass.pt")

vi=input("Use camera? (y/n): ")
if vi.lower() == 'y':
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    print(" Camera connected")
elif vi.lower() == 'h':    
   cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:    
    print("⚠ Camera not found → using video file")
    cap = cv2.VideoCapture(resource_path("video/grass.mp4"))
    
fps = cap.get(cv2.CAP_PROP_FPS)
print("="*54)
print("|"+" "*52+"|")
print("|"+" "*18 + "Camera FPS:", str(fps) + " "*18+"|")
print("|"+" "*52+"|")
print("="*54)
# ==========================================
# HELPER FUNCTIONS
# ==========================================
def in_bounds(x, y):
    return 0 <= x < GRID_SIZE_X and 0 <= y < GRID_SIZE_Y

def start_blade():
    global blade_on
    blade_on = True

def stop_blade():
    global blade_on
    blade_on = False

def toggle_machine():
    global machine_on
    machine_on = not machine_on
    if machine_on==False:
        send_direction("STOP")
        # print("Sent: STOP")
    else:
        send_direction("START") 
        # print("Sent: START")  
    print(" MACHINE ON" if machine_on else " MACHINE OFF")


# MANUAL OBSTACLE

def create_manual_obstacle():
    dx = 1 if robot_dir == "E" else -1 if robot_dir == "W" else 0
    dy = -1 if robot_dir == "N" else 1 if robot_dir == "S" else 0

    front_x = robot_x + dx
    front_y = robot_y + dy

    if in_bounds(front_x, front_y):
        grid[front_y, front_x] = 1
        print(" Manual Obstacle Created at:", front_x, front_y)


# BFS PATH TO NEAREST UNVISITED CELL

def find_path_to_unvisited():
    visited = set()
    queue = deque()
    queue.append((robot_x, robot_y, []))
    visited.add((robot_x, robot_y))

    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    while queue:
        x, y, path = queue.popleft()

        if grid[y, x] == 0:
            return path

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and grid[ny, nx] != 1 and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny, path + [(nx, ny)]))

    return None

def check_coverage_complete():
    global machine_on, coverage_complete
    if not np.any(grid == 0):
        coverage_complete = True
        machine_on = False
        stop_blade()
        send_direction("STOP")
        # send_direction("COMPLET")
        print("FLOOR FULLY COVERED")
        print('\a')


# FULL COVERAGE MOVEMENT

def coverage_move():
    global robot_x, robot_y, current_path,robot_dir

    grid[robot_y, robot_x] = 2
    start_blade()
   
    if current_path:
        nx, ny = current_path.pop(0)

        if nx > robot_x:
            robot_dir = "E"
        elif nx < robot_x:
            robot_dir = "W"
        elif ny > robot_y:
            robot_dir = "S"
        elif ny < robot_y:
            robot_dir = "N"

        robot_x, robot_y = nx, ny
        send_direction(robot_dir)
        return

    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    for dx, dy in directions:
        nx, ny = robot_x + dx, robot_y + dy
        if in_bounds(nx, ny) and grid[ny, nx] == 0:
            if nx > robot_x:
                robot_dir = "E"
            elif nx < robot_x:
                robot_dir = "W"
            elif ny > robot_y:
                robot_dir = "S"
            elif ny < robot_y:
                robot_dir = "N"
            robot_x, robot_y = nx, ny
            send_direction(robot_dir)
            return
    # print("Sent:",robot_dir)
    path = find_path_to_unvisited()

    if path:
        current_path = path
        robot_x, robot_y = current_path.pop(0)
    else:
        machine_on = False
        stop_blade()
        send_direction("STOP")
        print(" FLOOR FULLY COVERED")
        print('\a')
        print(" COVERAGE COMPLETE")


# OBSTACLE AVOIDANCE

def avoid_obstacle():
    global current_path, robot_x, robot_y,robot_dir
    # Mark front cell as obstacle
    dx = 1 if robot_dir == "E" else -1 if robot_dir == "W" else 0
    dy = -1 if robot_dir == "N" else 1 if robot_dir == "S" else 0

    front_x = robot_x + dx
    front_y = robot_y + dy

    if in_bounds(front_x, front_y) and grid[front_y, front_x] == 0:
        grid[front_y, front_x] = 1
        print(" Obstacle marked at:", front_x, front_y)

    new_path = find_path_to_unvisited()
    if new_path:
        current_path = new_path

        nx, ny = current_path.pop(0)

        if nx > robot_x:
            robot_dir = "E"
        elif nx < robot_x:
            robot_dir = "W"
        elif ny > robot_y:
            robot_dir = "S"
        elif ny < robot_y:
            robot_dir = "N"

        robot_x, robot_y = nx, ny
        send_direction(robot_dir)
        print(" New path calculated")
        # print("Sent:",robot_dir)
    else:
        print(" No alternate path found")


# DRAW GRID
def draw_grid():
    margin = 40
    img = np.ones((GRID_SIZE_Y*CELL_SIZE + margin,
                   GRID_SIZE_X*CELL_SIZE + margin, 3),
                   dtype=np.uint8) * 255

    for y in range(GRID_SIZE_Y):
        for x in range(GRID_SIZE_X):

            top_left = (x*CELL_SIZE + margin,
                        y*CELL_SIZE + margin)
            bottom_right = ((x+1)*CELL_SIZE + margin,
                            (y+1)*CELL_SIZE + margin)

            if grid[y,x] == 1:
                cv2.rectangle(img, top_left, bottom_right, (0,0,0), -1)
            elif grid[y,x] == 2:
                cv2.rectangle(img, top_left, bottom_right, (0,255,255), -1)

            cv2.rectangle(img, top_left, bottom_right, (200,200,200), 1)

    r1 = (robot_x*CELL_SIZE + margin,
          robot_y*CELL_SIZE + margin)
    r2 = ((robot_x+1)*CELL_SIZE + margin,
          (robot_y+1)*CELL_SIZE + margin)

    cv2.rectangle(img, r1, r2, (0,0,255), -1)

    return img


# MAIN LOOP

print("SMART CUTTER RUNNING")
last_move_time = time.time()
prev_time = time.time()
while True:
    read_nano_signal() 
   
    ret, frame = cap.read()
    if not ret:
        print(" Video ended → stopping machine")

        machine_on = False
        coverage_complete = True

        stop_blade()
        send_direction("STOP")
        break
    frame = cv2.resize(frame, (640, 640))
  
    frame_counter += 1
   
    current_time1 = time.time()
    fps = 1 / (current_time1 - prev_time)
    prev_time = current_time1

    cv2.putText(frame,f"FPS:{int(fps)}",(25,40),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
 
    
  
    run_detection = frame_counter % frame_skip == 0
    animal_detected = False
    obstacle_detected = False
    grass_detected = False

    if run_detection:
   
        results = model(frame, conf=0.5, verbose=False, half=True,device=0)
        resultsGrass = modelGrass(frame, conf=0.5, verbose=False, half=True,device=0)
        frame_center_x = frame.shape[1] // 2

        for r in results:
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                x1,y1,x2,y2 = map(int, box.xyxy[0])

                pixel_height = y2 - y1
                object_center_x = (x1 + x2) // 2

                # if pixel_height > 120 and abs(object_center_x - frame_center_x) < 100:
                if pixel_height > 180 and abs(object_center_x - frame_center_x) < 60:
                    if label in ANIMAL_CLASSES:
                        animal_detected = True
                    elif label in OBSTACLE_CLASSES:
                        obstacle_detected = True

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
                cv2.putText(frame,label,(x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)

        # ================= GRASS DETECTION =================
        for r in resultsGrass:
            for box in r.boxes:
                label = modelGrass.names[int(box.cls[0])]
                x1,y1,x2,y2 = map(int, box.xyxy[0])

                pixel_height = y2 - y1
                object_center_x = (x1 + x2) // 2

                
                if pixel_height > 180 and abs(object_center_x - frame_center_x) < 60:
                    if label == "grass":
                        grass_detected = True
                    if label == "other":
                        obstacle_detected = True

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,255),2)
                cv2.putText(frame,label,(x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,255),2)

            # ================= DECISION MAKING =================
        current_time = time.time()
        if (obstacle_detected or animal_detected or grass_detected):
            print('Not inside the grid \n',"DEBUG → animal:", animal_detected,
              "\nobstacle:", obstacle_detected,
              "\ngrass:", grass_detected,
              "\nwaiting:", waiting_for_turn)
            # 
        if not emergency_stop and machine_on and not coverage_complete and not waiting_for_turn:
         if current_time - last_move_time >= MOVE_DELAY:


            print("DEBUG → animal:", animal_detected,
              "obstacle:", obstacle_detected,
              "grass:", grass_detected,
              "waiting:", waiting_for_turn)
            if animal_detected:
                stop_blade()
                send_direction("STOP")
                cv2.putText(frame, "ANIMAL DETECTED - STOP",
                            (40,100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0,0,255), 3)
            
            elif obstacle_detected:
                avoid_obstacle()
                
                last_move_time = current_time



            else:
                if grass_detected:
                    coverage_move()
                    last_move_time = current_time
                else:
                    stop_blade()
                    avoid_obstacle()
                    coverage_move()
                    last_move_time = current_time
                    
                    cv2.putText(frame, "NO GRASS - SKIPPING",
                                (40,140),
                                cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (255,0,0), 3)

         check_coverage_complete()

    grid_img = draw_grid()

    status_text = "ON " if machine_on else "OFF "
    cv2.putText(grid_img, f"Machine: {status_text}",
                (20,30), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0,0,255), 2)

    if coverage_complete:
        cv2.putText(grid_img, "FLOOR COMPLETED!",
                    (150,30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0,0,255), 2)

    cv2.imshow("Camera", frame)
    cv2.imshow("Grid", grid_img)
    
    time.sleep(MOVE_DELAY)

    key = cv2.waitKey(1)

    if key == 27:
        send_direction("STOP"      )
        break
    elif key in [ord('o'), ord('O')]:
        create_manual_obstacle()
    elif key in [ord('m'), ord('M')]:
        toggle_machine()

cap.release()
if nano:
    nano.close()
cv2.destroyAllWindows()