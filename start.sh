#!/bin/bash
# Start virtual screen
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Start window manager
fluxbox > /dev/null 2>&1 &

# Run your untouched PySide6 app
python main.py &

# Stream to browser on Render's dynamic port
websockify --web=/usr/share/novnc/ ${PORT:-10000} localhost:5900