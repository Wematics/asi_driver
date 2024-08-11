import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# Load the .npz file
npz_file_path = '20240811221021.npz'
npz_data = np.load(npz_file_path, allow_pickle=True)

# List all the array names in the .npz file
print("Arrays in the .npz file:")
array_names = [name for name in npz_data.keys() if 'metadata' not in name]

for array_name in array_names:
    # Convert the array into bytes, then interpret those bytes as 16-bit data
    array = npz_data[array_name].view('uint16')

    # Create a new figure for the array
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the image with logarithmic normalization
    im = ax.imshow(array, cmap='jet', norm=LogNorm())
    ax.set_title(array_name)

    # Set x-axis and y-axis labels
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')

    # Remove the axis ticks
    ax.set_xticks([])
    ax.set_yticks([])

    # Calculate and print the min, max, and average of the array
    shape = array.shape
    array_min = np.min(array)
    array_max = np.max(array)
    array_mean = np.mean(array)
    print(f"For {array_name}, Min: {array_min}, Max: {array_max}, Avg: {array_mean}, shape: {shape}")

    # Create a colorbar legend on the right side
    cbar = fig.colorbar(im)
    cbar.ax.set_ylabel('Colorbar Label')

    # Save the plot as an image file
    plt.savefig(f"{array_name}.png")
    plt.close()  # Close the plot to free memory

    print(f"Plot saved as {array_name}.png")

print("All plots saved successfully.")
