from picamera2 import Picamera2
import numpy as np
import datetime
import time

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

    exposure_list = [50000000, 80000000, 100000000]  # 50s in microseconds

    for exposure_time in exposure_list:
        picam2.set_controls({"ExposureTime": exposure_time, "AnalogueGain": 8.0})

        # Sleep for the exposure time to ensure it's fully processed
        time.sleep(exposure_time / 1000000 + 2)  # Extra buffer for safety

        request = picam2.capture_request()

        # Capture raw image and store metadata
        images[f'{timestamp}_{exposure_time}'] = request.make_array("raw")
        metadata.append((f'{timestamp}_{exposure_time}', request.get_metadata()))

        request.release()

    picam2.stop()

# Convert metadata list to structured numpy array
dtypes = [('timestamp_exp', 'U20')] + [(key.replace(' ', '_'), 'U100') for key in metadata[0][1].keys()]
metadata_array = np.zeros(len(metadata), dtype=dtypes)
for i, (timestamp_exp, meta) in enumerate(metadata):
    metadata_array[i]['timestamp_exp'] = timestamp_exp
    for key in meta.keys():
        metadata_array[i][key.replace(' ', '_')] = str(meta[key])

# Save images and metadata to npz file
np.savez(f'{timestamp}.npz', **images, **{f'{timestamp}_metadata': metadata_array})

print(f"Capture completed. Images and metadata saved as {timestamp}.npz")
