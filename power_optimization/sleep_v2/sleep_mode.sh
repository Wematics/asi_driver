#!/bin/bash

# Define variables
SERVICE_NAME="sleep-mode"
TIMER_NAME="sleep-mode"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
TIMER_PATH="/etc/systemd/system/${TIMER_NAME}.timer"
SCRIPT_PATH="/home/pi/Desktop/skycam/scripts/sleep/check_sun_times.py"
WORKING_DIR="/home/pi/Desktop/skycam/scripts/sleep"
LOG_FILE="${WORKING_DIR}/sleep_wake.log"
CONFIG_FILE="${WORKING_DIR}/config.json"

# Create the systemd service file
echo "Creating systemd service file..."
sudo bash -c "cat > ${SERVICE_PATH}" <<EOL
[Unit]
Description=Sleep Mode Service for SkyCam
After=network.target

[Service]
ExecStart=/home/pi/Desktop/skycam/scripts/sleep/check_sun_times.py
WorkingDirectory=/home/pi/Desktop/skycam/scripts/sleep
StandardOutput=syslog
StandardError=syslog
Restart=on-failure
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOL

# Create the systemd timer file
echo "Creating systemd timer file..."
sudo bash -c "cat > ${TIMER_PATH}" <<EOL
[Unit]
Description=Run SkyCam Sleep Mode Script Periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Unit=sleep-mode.service

[Install]
WantedBy=timers.target
EOL

# Reload systemd to apply the new service and timer
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start the timer
echo "Enabling and starting the timer..."
sudo systemctl enable ${TIMER_NAME}.timer
sudo systemctl start ${TIMER_NAME}.timer

# Check the status of the service and timer
echo "Checking status of the service and timer..."
sudo systemctl status ${TIMER_NAME}.timer
sudo systemctl status ${SERVICE_NAME}.service

# Notify the user
echo "Service and timer setup completed. The sleep mode script is now scheduled to run periodically."
