#!/bin/bash

# Define variables
SERVICE_NAME="sleep-mode"
TIMER_NAME="sleep-mode"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
TIMER_PATH="/etc/systemd/system/${TIMER_NAME}.timer"
SCRIPT_PATH="/home/pi/Desktop/skycam/scripts/sleep/check_sun_times.py"
WORKING_DIR="/home/pi/Desktop/skycam/scripts/sleep"

# Ensure the script exists
if [ ! -f "${SCRIPT_PATH}" ]; then
    echo "Error: Script ${SCRIPT_PATH} not found!"
    exit 1
fi

# Create the systemd service file
echo "Creating systemd service file..."
sudo bash -c "cat > ${SERVICE_PATH}" <<EOL
[Unit]
Description=Sleep Mode Service for SkyCam
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${SCRIPT_PATH}
WorkingDirectory=${WORKING_DIR}
StandardOutput=journal
StandardError=journal
Restart=on-failure
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOL

# Verify service file creation
if [ -f "${SERVICE_PATH}" ]; then
    echo "Service file created successfully at ${SERVICE_PATH}"
else
    echo "Error: Failed to create service file."
    exit 1
fi

# Create the systemd timer file
echo "Creating systemd timer file..."
sudo bash -c "cat > ${TIMER_PATH}" <<EOL
[Unit]
Description=Run SkyCam Sleep Mode Script Periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=10min
Unit=${SERVICE_NAME}.service

[Install]
WantedBy=timers.target
EOL

# Verify timer file creation
if [ -f "${TIMER_PATH}" ]; then
    echo "Timer file created successfully at ${TIMER_PATH}"
else
    echo "Error: Failed to create timer file."
    exit 1
fi

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
echo "Service and timer setup completed. The sleep mode script is now scheduled to run every 10 minutes."
