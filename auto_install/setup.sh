#!/bin/bash

# Update and install necessary packages
sudo apt-get update
sudo apt-get install -y python3-full python3-pip python3-dev python3-venv libgpiod2 gpsd gpsd-clients device-tree-compiler

# Create and activate virtual environment
python3 -m venv asi_venv
source asi_venv/bin/activate

# Check if requirements.txt exists and install Python packages
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found"
    exit 1
fi

# Create and compile Device Tree Overlay for EMC2301 (Fan)
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
sudo sed -i '$ a dtoverlay=emc2301-overlay' /boot/firmware/config.txt

# Create and compile Device Tree Overlay for LM75 (Temperature Sensor)
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
sudo sed -i '$ a dtoverlay=lm75-overlay' /boot/firmware/config.txt

# Create systemd service to set fan speed at boot
sudo tee /etc/systemd/system/set-fan-speed.service > /dev/null <<EOF
[Unit]
Description=Set Fan Speed to Maximum at Boot
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo 255 | sudo tee /sys/class/hwmon/hwmon2/pwm1'

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable set-fan-speed.service
sudo systemctl start set-fan-speed.service

# Reboot to apply changes
sudo reboot
