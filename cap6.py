import os
import subprocess
import logging
from datetime import datetime, timedelta
import shutil
import json
from pathlib import Path
import asi_sens  # Import the sensor module
from multiprocessing import Process, Manager

camera_name = "Camera1"

class SkyCam:
    def __init__(self):
        self.PRE_HDR = Path("/home/pi/skycam/images")
        self.LOG_DIR = Path("/home/pi/skycam/logs")
        self.META_FILE = self.PRE_HDR / "metadata.txt"
        self.EXIF_CONFIG_FILE = Path("/home/pi/asi_driver/exif.config")

    def capture_image(self, date):
        output_file = self.PRE_HDR / f"{date}.jpg"
        self.PRE_HDR.mkdir(parents=True, exist_ok=True)

        # Capture the image and metadata
        self.capture_with_metadata(output_file)
        
        metadata = self.read_metadata()
        logging.info(f"Image {date} captured with metadata: {metadata}.")
        return output_file, metadata

    def capture_with_metadata(self, output_file):
        result = subprocess.run(
            [
                "libcamera-still",
                "-o", str(output_file),
                "--tuning-file", "/usr/share/libcamera/ipa/rpi/pisp/imx477_noir.json",
                "--ev", "-2",
                "--post-process-file", "/home/pi/skycam/scripts/hdr.json",
                "--immediate",
                "--width", "3280",
                "--height", "2464",
                "-n",
                "--metadata", str(self.META_FILE)
            ],
            capture_output=True,
            text=True
        )

    def read_metadata(self):
        with open(self.META_FILE, 'r') as f:
            metadata = json.load(f)
        print("Captured Metadata:\n", metadata)  # Print full metadata
        return metadata

def create_save_path():
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    hour = now.strftime("%H")
    base_path = f"/media/pi/79CA-AFF6/Dataset/{year}/{camera_name}/{month}/{day}/{hour}"
    os.makedirs(base_path, exist_ok=True)

    statvfs = os.statvfs('/media/pi/79CA-AFF6')
    free_space = statvfs.f_frsize * statvfs.f_bavail
    if free_space < 1e9:
        print(f"Not enough space on USB stick! Free space: {free_space/1e9:.2f} GB")
        oldest_time = datetime.now() - timedelta(days=7)
        for dirpath, dirnames, filenames in os.walk('/media/pi/79CA-AFF6/Dataset'):
            if datetime.fromtimestamp(os.path.getmtime(dirpath)) < oldest_time:
                print(f"Deleting directory: {dirpath}")
                shutil.rmtree(dirpath)
        for dirpath, dirnames, filenames in os.walk(base_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if datetime.fromtimestamp(os.path.getmtime(file_path)) < oldest_time:
                    print(f"Deleting file: {file_path}")
                    os.remove(file_path)

    return base_path

def save_image_with_custom_exif(image_path, metadata, exif_config_file):
    exif_tags = []
    for key, value in metadata.items():
        if key not in ["description", "camera", "date"]:
            tag = f"-EXIF:{key}={value}"
            exif_tags.append(tag)
            print(f"Setting EXIF tag {key} to {value}")
    try:
        subprocess.run(
            [
                "exiftool",
                "-config", str(exif_config_file),
                *exif_tags,
                str(image_path)
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error setting EXIF tags: {e}")
    except Exception as e:
        print(f"Unexpected error setting EXIF tags: {e}")

def capture_and_save_image(skycam, date, return_dict):
    image_path, metadata = skycam.capture_image(date)
    save_path = create_save_path()
    final_image_path = os.path.join(save_path, f"{date}.jpg")
    shutil.copy2(str(image_path), final_image_path)
    os.remove(str(image_path))
    return_dict['image_path'] = final_image_path
    return_dict['metadata'] = metadata

def main():
    manager = Manager()
    return_dict = manager.dict()
    skycam = SkyCam()
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    capture_process = Process(target=capture_and_save_image, args=(skycam, date, return_dict))
    capture_process.start()
    
    # Simultaneously read sensor data
    sensor_data = asi_sens.get_sensor_data()
    capture_process.join()
    
    final_image_path = return_dict['image_path']
    metadata = return_dict['metadata']
    
    # Update metadata with additional sensor data
    metadata.update(sensor_data)

    metadata.update({
        "description": "Sky image",
        "camera": camera_name,
        "date": date,
    })

    # Save EXIF tags
    save_image_with_custom_exif(final_image_path, metadata, skycam.EXIF_CONFIG_FILE)
    print(f"Image saved with metadata at: {final_image_path}")

if __name__ == "__main__":
    main()
