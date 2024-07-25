import os

def read_fan_speed():
    hwmon_path = "/sys/class/hwmon"
    
    # Find the hwmon directory that contains fan1_input
    for root, dirs, files in os.walk(hwmon_path):
        for name in files:
            if name == "fan1_input":
                fan_speed_path = os.path.join(root, name)
                try:
                    with open(fan_speed_path, 'r') as f:
                        fan_speed = f.read().strip()
                        return int(fan_speed)
                except Exception as e:
                    print(f"Error reading fan speed: {e}")
                    return None
    
    print("fan1_input not found in /sys/class/hwmon/")
    return None

if __name__ == "__main__":
    fan_speed = read_fan_speed()
    if fan_speed is not None:
        print(f"Current fan speed: {fan_speed} RPM")
    else:
        print("Failed to read fan speed.")
