import os
import sys

from collections import Counter

from skimage.segmentation import felzenszwalb
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float

import cv2
import numpy as np

def remove_small_particles(min_size, label_mask, label_counts):
    new_mask = np.copy(label_mask)
    for label, count in label_counts:
        if label == 0:
            continue
        elif count < min_size:
            new_mask[new_mask == label] = 0
    new_mask[new_mask != 0] = 255
    return new_mask.astype("uint8")

def load_and_preprocess_image(image_path):
    
    # Read
    img = cv2.imread(image_path, 
                    cv2.IMREAD_GRAYSCALE)
    img_color = cv2.imread(image_path)
    
    # Normalize
    img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

    # Filter
    median = cv2.medianBlur(img_norm, 7)

    return img_color, img, median

def adaptive_threshold(preprocessed_image):
    # Threshold
    thresh = cv2.adaptiveThreshold(preprocessed_image,
                                   255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY,
                                   13,
                                   2)
    # We are interested in the black parts
    not_thresh = 255 - thresh
    return not_thresh

def remove_border_lines(binary_image):
    negative = 255 - binary_image

    # Remove horizontal borders
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25,1))
    detected_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(negative, [c], -1, (255,255,255), 2)

    # Remove vertical borders
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,25))
    detected_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    cnts = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(negative, [c], -1, (255,255,255), 2)

    unbordered_image = 255 - negative

    return unbordered_image

def superpixel_segmentation(binary_image):
    binary_image_float = img_as_float(binary_image)
    segments_fz = felzenszwalb(binary_image_float, scale=100, sigma=0.5, min_size=50)
    c = Counter(segments_fz.flatten())
    background_label = max(c, key=c.get)
    superpixel_mask = (segments_fz != background_label).astype("uint8") * 255
    return superpixel_mask

def connected_components(binary_image):
    qty, label_mask = cv2.connectedComponents(binary_image)
    labels, counts = np.unique(label_mask, return_counts=True)
    label_counts = [*zip(labels, counts)]
    label_counts.sort(key=lambda x:x[1], reverse=True)

    return qty, label_mask, label_counts


def clean_artifacts(binary_image, particle_threshold=10000):
    qty, label_mask, label_counts = connected_components(binary_image)

    # Reference segmentation using superpixels
    # TODO: Avoid arbitrary sizes (why 10000?)
    clean_label_mask = remove_small_particles(particle_threshold, label_mask, label_counts)

    return clean_label_mask

def connect_close_blobs(binary_image):

    # Fill holes with morphology
    N8 = np.ones((3, 3))

    # TODO: Using arbitrary filters
    dilatacion = cv2.dilate(binary_image, N8, iterations=10)
    
    erosion = cv2.erode(dilatacion, N8, iterations=5)

    return erosion
