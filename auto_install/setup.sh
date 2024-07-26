#!/bin/bash

echo "Starting setup script..."

# Disable Bluetooth
echo "Disabling Bluetooth to reduce power consumption..."
sudo systemctl disable bluetooth
sudo systemctl disable bthelper@.service

# Enable VNC, I2C, and serial in raspi-config
echo "Enabling VNC, I2C, and serial in raspi-config..."
sudo raspi-config nonint do_vnc 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 2

# Update and install necessary packages
echo "Updating package list and installing necessary packages..."
sudo apt-get update
sudo apt-get install -y python3-full python3-pip python3-dev python3-venv exiftool libgpiod2 gpsd gpsd-clients device-tree-compiler git

# Clone the GitHub repository
if [ ! -d "asi_driver" ]; then
    echo "Cloning GitHub repository..."
    git clone https://github.com/Wematics/asi_driver.git
else
    echo "GitHub repository already exists. Skipping clone."
fi

cd asi_driver || { echo "Failed to enter asi_driver directory"; exit 1; }

# Create and activate virtual environment
echo "Creating and activating virtual environment..."
python3 -m venv asi_venv
source asi_venv/bin/activate

# Add alias to ~/.bashrc
if ! grep -q "alias sky=" ~/.bashrc; then
    echo "Adding alias 'sky' to ~/.bashrc..."
    echo "alias sky='cd ~/asi_driver && source asi_venv/bin/activate'" >> ~/.bashrc
    echo "Alias 'sky' added to ~/.bashrc"
else
    echo "Alias 'sky' already exists in ~/.bashrc. Skipping."
fi

# Source the ~/.bashrc to apply the alias immediately
echo "Sourcing ~/.bashrc to apply alias..."
source ~/.bashrc

# Check if requirements.txt exists and install Python packages
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found"
    exit 1
fi

# Update GPSD configuration
echo "Updating GPSD configuration..."
sudo tee /etc/default/gpsd > /dev/null <<EOF
DEVICES="/dev/ttyAMA3"
GPSD_OPTIONS="-n"
USBAUTO="true"
EOF

# Enable UART for GPS
echo "Enabling UART for GPS..."
if ! grep -q "dtoverlay=uart3" /boot/firmware/config.txt; then
    sudo sed -i '$ a dtoverlay=uart3' /boot/firmware/config.txt
else
    echo "UART for GPS already enabled in config.txt"
fi

# Create and compile Device Tree Overlay for LM75 (Temperature Sensor)
echo "Creating and compiling Device Tree Overlay for LM75..."
cat <<EOF > lm75-overlay.dts
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2835";

    fragment@0 {
        target = <&i2c1>;
        __overlay__ {
            #address-cells = <1>;
            #size-cells = <0>;

            lm75: lm75@48 {
                compatible = "national,lm75";
                reg = <0x48>;
            };
        };
    };
};
EOF

dtc -@ -I dts -O dtb -o lm75-overlay.dtbo lm75-overlay.dts
sudo cp lm75-overlay.dtbo /boot/firmware/overlays/

# Add dtoverlay=lm75-overlay to config.txt if not already present
if ! grep -q "dtoverlay=lm75-overlay" /boot/firmware/config.txt; then
    sudo sed -i '$ a dtoverlay=lm75-overlay' /boot/firmware/config.txt
else
    echo "Device Tree Overlay for LM75 already present in config.txt"
fi

# Create and compile Device Tree Overlay for EMC2301 (Fan)
echo "Creating and compiling Device Tree Overlay for EMC2301..."
cat <<EOF > emc2301-overlay.dts
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2835";

    fragment@0 {
        target = <&i2c1>;
        __overlay__ {
            #address-cells = <1>;
            #size-cells = <0>;

            emc2301: emc2301@2f {
                compatible = "microchip,emc2301";
                reg = <0x2f>;
                #cooling-cells = <2>;
            };
        };
    };
};
EOF

dtc -@ -I dts -O dtb -o emc2301-overlay.dtbo emc2301-overlay.dts
sudo cp emc2301-overlay.dtbo /boot/firmware/overlays/

# Add dtoverlay=emc2301-overlay to config.txt if not already present
if ! grep -q "dtoverlay=emc2301-overlay" /boot/firmware/config.txt; then
    sudo sed -i '$ a dtoverlay=emc2301-overlay' /boot/firmware/config.txt
else
    echo "Device Tree Overlay for EMC2301 already present in config.txt"
fi

# Create systemd service to set fan speed at boot
echo "Creating systemd service to set fan speed at boot..."
sudo tee /etc/systemd/system/set-fan-speed.service > /dev/null <<EOF
[Unit]
Description=Set Fan Speed to Maximum at Boot
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo 255 | sudo tee /sys/class/hwmon/hwmon3/pwm1'

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable set-fan-speed.service
sudo systemctl start set-fan-speed.service

echo "Setup complete. System will now reboot to apply changes."
# Ask the user if they want to reboot now
read -p "Setup complete. Do you want to reboot now? (y/n): " choice
case "$choice" in 
  y|Y ) echo "Rebooting now..."; sudo reboot;;
  n|N ) echo "Reboot cancelled. Please reboot manually to apply changes.";;
  * ) echo "Invalid input. Please reboot manually to apply changes.";;
esac
