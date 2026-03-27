# Smart Grass Cutter Robot 🤖🌱

An AI-powered autonomous grass cutting robot using:

 - YOLOv8 (Object Detection) 🎯

 - Custom Grass Detection Model 🌱

 - OpenCV (Computer Vision) 📷

 - Arduino Nano (Motor Control via Serial) 🔌

 - Python (Path Planning + Control Logic) 🧠
## Features
- Full area coverage using grid-based movement
- BFS path finding for intelligent navigation
- Animal detection → stops machine instantly
- Obstacle detection → auto reroute
- Grass detection → cut only where needed
- Real-time camera/video processing
- Arduino communication via serial (COM port)

## Setup
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt 

## Run
python main.py