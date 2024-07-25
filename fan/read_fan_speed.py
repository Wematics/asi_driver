import os

def read_fan_speed():
    fan_speed_path = "/sys/class/hwmon/hwmon2/pwm1"
    
    try:
        with open(fan_speed_path, 'r') as f:
            fan_speed = f.read().strip()
            return int(fan_speed)
    except Exception as e:
        print(f"Error reading fan speed: {e}")
        return None

if __name__ == "__main__":
    fan_speed = read_fan_speed()
    if fan_speed is not None:
        print(f"Current fan speed: {fan_speed} (PWM value)")
    else:
        print("Failed to read fan speed.")
