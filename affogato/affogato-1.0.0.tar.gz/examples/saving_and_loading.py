import numpy as np
import affogato.data as af_data

"""
Example of saving and loading features in affogato.

This file loads some labeled images, scales it, and saves it as a numpy zip file.
"""


print(
    """
Enter a path to a directory containing images.
The directory structure should be as follows:
root
├── 0
│   ├── 0.png
│   ├── 1.png
│   ├── 2.png
│   ...
├── 1
│   ├── 0.png
│   ...
├── 2
│   ├── 0.png
│   ...
...
    """
    .strip()
)
path = input("Enter the path to the images: ")
gray_scale = input("Are the images grayscale? (y/N): ").lower() == "y"


print("Loading images...")
labeled_images = af_data.labeled_image_directory(
        path,
        gray_scale=gray_scale,
        verbose=True,
        )

# Scale the pixels to be between 0 and 1
print("Scaling images...")
scaled_labeled_images = [ (image / 255.0, l) for image, l in labeled_images ]

# Save the images in the save path as a numpy zip file
save_path = path + ".npz"
print(f"Saving images to {save_path}...")
af_data.save_numpy_file(save_path, scaled_labeled_images)

# Make sure the images are loaded correctly
print("Checking images are loaded correctly...")
loaded_images = af_data.numpy_file(save_path)
for (image, l), (loaded_image, loaded_l) in zip(scaled_labeled_images, loaded_images):
    assert np.array_equal(image, loaded_image)
    assert np.array_equal(l, loaded_l)

print("Images are loaded correctly!")

