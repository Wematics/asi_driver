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

with Picamera2() as picam2:
    # Configure the camera for full resolution
    config = picam2.create_still_configuration(
        main={"size": (4056, 3040), "format": "RGB888"},
        raw={"format": "SRGGB12", "size": (4056, 3040)}
    )
    picam2.configure(config)
    picam2.start()

    exposure_list = [55000000, 60000000, 65000000]  # 50s, 80s, 100s in microseconds

    for exposure_time in exposure_list:
        picam2.set_controls({"ExposureTime": exposure_time, "AnalogueGain": 8.0})

        # Sleep for the exposure time to ensure it's fully processed
        time.sleep(exposure_time / 1000000 + 2)  # Extra buffer for safety

        request = picam2.capture_request()

        # Capture raw image and store metadata
        actual_exp_time = request.get_metadata()["ExposureTime"]
        image_key = f'{timestamp}_exp{actual_exp_time}'
        images[image_key] = request.make_array("raw")
        metadata.append((image_key, request.get_metadata()))

        request.release()

        # Log and print that the frame was captured
        log_message = f"Captured frame with exposure time {actual_exp_time} microseconds."
        logging.info(log_message)
        print(log_message)

    picam2.stop()

# Sort metadata by exposure time to ensure the order is correct
metadata.sort(key=lambda x: int(x[0].split('_exp')[-1]))

# Convert metadata list to structured numpy array
dtypes = [('timestamp_exp', 'U20')] + [(key.replace(' ', '_'), 'U100') for key in metadata[0][1].keys()]
metadata_array = np.zeros(len(metadata), dtype=dtypes)
for i, (timestamp_exp, meta) in enumerate(metadata):
    metadata_array[i]['timestamp_exp'] = timestamp_exp
    for key in meta.keys():
        metadata_array[i][key.replace(' ', '_')] = str(meta[key])

# Save images and metadata to npz file
np.savez(f'{timestamp}.npz', **images, **{f'{timestamp}_metadata': metadata_array})

final_message = f"Capture completed. Images and metadata saved as {timestamp}.npz"
logging.info(final_message)
print(final_message)
