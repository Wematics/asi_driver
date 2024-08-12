import logging
from picamera2 import Picamera2
import numpy as np
import datetime
import time

# Set up logging
log_filename = "capture_log.txt"
logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
images = {}
metadata = []

# Set up the desired exposure times
exposure_list = [5000000, 55000000, 60000000, 65000000]  # 55s, 60s, 65s in microseconds

for exposure_time in exposure_list:
    try:
        # Initialize and configure the camera for each frame
        picam2 = Picamera2()
        config = picam2.create_still_configuration(
            main={"size": (4056, 3040), "format": "RGB888"},
            raw={"format": "SRGGB12", "size": (4056, 3040)}
        )
        picam2.configure(config)
        
        # Start the camera
        picam2.start()
        
        # Set the frame duration and controls
        picam2.set_controls({
            "ExposureTime": exposure_time, 
            "AnalogueGain": 8.0,
            "FrameDurationLimits": (100000000, 100000000)  # 100s in microseconds
        })

        # Wait briefly to ensure the settings are fully applied
        time.sleep(2)  # Short delay to ensure the settings are applied

        # Capture the first frame to ensure settings are applied (optional)
        request = picam2.capture_request()
        request.release()

        # Sleep for the duration of the exposure to ensure it's fully processed
        time.sleep(exposure_time / 1000000 + 2)  # Ensure exposure completes

        request = picam2.capture_request()

        # Capture raw image and store metadata
        actual_exp_time = request.get_metadata()["ExposureTime"]
        image_key = f'{timestamp}_exp{actual_exp_time}'
        images[image_key] = request.make_array("raw")
        metadata.append((image_key, request.get_metadata()))

        # Immediately print the exposure time after capturing the frame
        print(f"Captured frame with exposure time {actual_exp_time} microseconds.")
        
        # Log the captured frame
        log_message = f"Captured frame with exposure time {actual_exp_time} microseconds."
        logging.info(log_message)

        request.release()

    finally:
        # Stop the camera and release resources after each capture
        picam2.stop()
        picam2.close()  # Explicitly close the camera to release all resources

# Sort metadata by exposure time to ensure the order is correct
metadata.sort(key=lambda x: int(x[0].split('_exp')[-1]))

# Determine the keys available in the metadata
all_keys = set(key.replace(' ', '_') for _, meta in metadata for key in meta.keys())

# Convert metadata list to structured numpy array
dtypes = [('timestamp_exp', 'U20')] + [(key, 'U100') for key in all_keys]
metadata_array = np.zeros(len(metadata), dtype=dtypes)

for i, (timestamp_exp, meta) in enumerate(metadata):
    metadata_array[i]['timestamp_exp'] = timestamp_exp
    for key in all_keys:
        # Only assign if the key exists in the current metadata
        if key in meta:
            metadata_array[i][key] = str(meta.get(key.replace('_', ' '), ''))

# Save images and metadata to npz file
np.savez(f'{timestamp}.npz', **images, **{f'{timestamp}_metadata': metadata_array})

final_message = f"Capture completed. Images and metadata saved as {timestamp}.npz"
logging.info(final_message)
print(final_message)
