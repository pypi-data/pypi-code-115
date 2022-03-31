from collections import OrderedDict

import matplotlib.pyplot as plt

from scipy.spatial import distance_matrix

from skimage.util import img_as_float

from sklearn.cluster import DBSCAN

import pandas as pd
import cv2

import numpy as np

try:
    from regions import Region
except:
    from huellas.regions import Region


def build_region_objects(cc_label_counts, label_mask, grayscale):
    regions = []
    i = 0
    for label, count in cc_label_counts:
        if label == 0 :
            continue
        cut_mask = label_mask == label
        
        # Calculate contours
        contours, _  = cv2.findContours(cut_mask.astype("uint8"), 
                                        cv2.RETR_EXTERNAL, 
                                        cv2.CHAIN_APPROX_SIMPLE)
       
        # Don't process images with less than one contour
        if len(contours) > 0:
            # Fill entire region as marked by contour
            cut_mask = cut_mask.astype("float32") * 255
            cut_mask = cv2.fillPoly(cut_mask, contours, 255)
            cut_mask = cut_mask == 255
            # Process region
            r = Region(contours[0], cut_mask, grayscale)
            regions.append((i, r))
            i +=1

    # Classification starts
    regions.sort(key=lambda x: x[1], reverse=True)
    
    return regions

def get_fingerprint_candidates(regions, border_height, border_width, img_height, img_width):
    f_candidates = []
    # Check for candidates in borders
    for i, region in regions:
        is_candidate = False
        w, h = region.centroid
        if h <= border_height or h >= img_height - border_height:
            is_candidate = True
        else:
            if w <= border_width or w >= img_width - border_width:
                is_candidate = True
        if is_candidate:
            # Check if it is square-like
            poly = region.approx_poly(0.05)
            if len(poly) == 4:
                # Check ratio
                max_value = max(region.rect[1])
                min_value = min(region.rect[1])
                ratio = max_value / min_value
                # Check size
                # TODO: Sizes shouldn't be hard-coded
                if ratio < 2 and max_value < 500 and min_value > 150:
                    f_candidates.append((i, region))
    
    # Check distance between all pairs and remove the ones that are too far away
    if len(f_candidates) > 1:
        candidate_centroids = []
        candidate_labels = []
        for i, region in f_candidates:
            candidate_centroids.append(region.centroid)
            candidate_labels.append(i)
        distances = distance_matrix(candidate_centroids, 
                                    candidate_centroids)
        distances_df = pd.DataFrame(distances, 
                                    index=candidate_labels, 
                                    columns=candidate_labels)
        candidate_labels = np.array(candidate_labels)
        # TODO: Distance cut-off shouldn't be hard-coded
        final_candidate_labels = candidate_labels[distances_df.quantile(.25) < 1000]
    else:
        # Assume that the single candidate is a false positive
        final_candidate_labels = []
    
    return f_candidates, final_candidate_labels

def save_fingerprint_candidates(f_candidates, final_candidate_labels, output_folder_path):

    all_paths = []
    for i, region in f_candidates:
        if i in final_candidate_labels:
            region.save_cropped(output_folder_path + "fprint%d.png" % i)
            all_paths.append(output_folder_path + "fprint%d.png" % i)
    all_paths.sort()
    return all_paths

def get_hand_candidates(regions, final_candidate_labels, img_height, img_width, BORDER_OFFSET):
    left_limit = BORDER_OFFSET
    right_limit = img_width - BORDER_OFFSET
    up_limit = BORDER_OFFSET
    down_limit = img_height - BORDER_OFFSET
    hand_candidates = []
    hand_region_coordinates = []
    # For every region not in final_candidate_labels, assume it may be part of a hand
    for i, region in regions:
        is_in_border = False
        if i not in final_candidate_labels:
            # Check if it's not a border artifact
            x_left, y_up = region.left_most_coordinate
            x_right, y_down = region.right_most_coordinate

            if x_left <= left_limit or x_right >= right_limit or\
                    y_up <= up_limit or y_down >= down_limit:
                        is_in_border = True

            if not is_in_border:
                hand_candidates.append((i, region))
                hand_region_coordinates.append(region.left_most_coordinate)
                hand_region_coordinates.append(region.right_most_coordinate)
    return hand_candidates, hand_region_coordinates

def remove_noncandidate_regions_from_mask(regions, candidates, mask):
    # Remove non-candidates from mask:
    candidates_ids = [i for i, _ in candidates]
    for i, region in regions:
        if i not in candidates_ids:
            (min_x, min_y) = region.left_most_coordinate
            (max_x, max_y) = region.right_most_coordinate
            
            mask[min_y:max_y, min_x:max_x] = 0
    return mask

def get_hand_bounding_box(hand_region_coordinates):
    # Get hand bounding box
    hand_region_coordinates.sort()
    min_x, _ = hand_region_coordinates[0]
    max_x, _ = hand_region_coordinates[-1]
    hand_region_coordinates.sort(key=lambda x: x[1])
    _, min_y = hand_region_coordinates[0]
    _, max_y = hand_region_coordinates[-1]
    hand_rect = (min_x, min_y, max_x-min_x, max_y-min_y)
    return min_x, min_y, max_x, max_y, hand_rect

def extract_hand(mask_1, mask_2, hand_region_coordinates, original):
    # Get region bounding box
    min_x, min_y, max_x, max_y, _ = get_hand_bounding_box(hand_region_coordinates)
    
    N8 = np.ones((3, 3))
    # Creating new mask on initial segmentation
    # TODO: using arbitrary filters
    hand_dilate = cv2.dilate(mask_1, N8, iterations=15)
    
    hand_erode = cv2.erode(hand_dilate, N8, iterations=5)

    # Cut regions in both simple and superpixel-clean segmentation (mask_2)
    hand_region = hand_erode[min_y:max_y, min_x:max_x]
    clean_hand_region = mask_2[min_y:max_y, min_x:max_x]
   
    # Count connected components in simple segmentation
    _, hand_label_mask = cv2.connectedComponents(hand_region)
   
    # Apply mask
    # twomask_combination is a labeling of connected components
    # resulting from the combination of the two masks
    twomask_combination = img_as_float(clean_hand_region) * hand_label_mask
    selected_components = np.unique(twomask_combination)
    selected_components = selected_components[selected_components != 0]
    for c in selected_components:
        hand_label_mask[hand_label_mask == c] = 255
    hand_label_mask[hand_label_mask != 255] = 0
    hand_label_mask = hand_label_mask.astype("uint8")
    
    color_hand_region = original[min_y:max_y, min_x:max_x]
    extracted_hand = cv2.bitwise_and(color_hand_region, color_hand_region, mask=hand_label_mask)

    return extracted_hand, hand_label_mask
