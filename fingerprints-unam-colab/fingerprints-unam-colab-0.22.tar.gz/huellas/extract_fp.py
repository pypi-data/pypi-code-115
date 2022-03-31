try:
    from extraction import *
except:
    from huellas.extraction import *

try:
    from segmentation import *
except:
    from huellas.segmentation import *

try:
    from auxiliar import *
except:
    from huellas.auxiliar import *

def main(input_img_path, output_folder_path, BORDER_OFFSET=100):

    progress_bar(100, 0)

    # Load and do inital processing
    original, grayscale, preprocessed = load_and_preprocess_image(input_img_path)
    progress_bar(100, 6)

    # Get image height/width
    img_height, img_width = grayscale.shape
    progress_bar(100, 12)

    bin_image = adaptive_threshold(preprocessed)
    progress_bar(100, 18)
   
    noborder_bin_image = remove_border_lines(bin_image)
    progress_bar(100, 24)

    superpixel_mask = superpixel_segmentation(noborder_bin_image) 
    progress_bar(100, 30)
   
    noartifacts_superpixel_mask = clean_artifacts(superpixel_mask)
    progress_bar(100, 36)
  
    clean_mask = connect_close_blobs(noartifacts_superpixel_mask)
    progress_bar(100, 42)
  
    # Map connected components in clean image
    qty, label_mask, label_counts = connected_components(clean_mask)
    progress_bar(100, 48)
    
    # Color connected components for visualization
    clean_blobs_color = colorear_componentes_conexas(label_mask)
    progress_bar(100, 54)

    # Transform components to Region objects
    regions = build_region_objects(label_counts, label_mask, grayscale)
    progress_bar(100, 60)
    
    # Number regions in color image and save
    for i, region in regions:
        cv2.putText(clean_blobs_color,
                    str(i),
                    region.centroid,
                    cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 255, 255), 2)
    guardar_imagen(clean_blobs_color, output_folder_path + "blob_numbers.png")
    progress_bar(100, 66)

    # Get isolated fingerprint candidates
    border_height = int(grayscale.shape[0]/4)
    border_width = int(grayscale.shape[1]/4)
    f_candidates, final_candidate_labels = get_fingerprint_candidates(
            regions, 
            border_height, 
            border_width, 
            img_height,
            img_width)
    progress_bar(100, 72)

    # Save remaining fingerprint candidates
    save_fingerprint_candidates(
            f_candidates, 
            final_candidate_labels, 
            output_folder_path)
    progress_bar(100, 78)

    # For every non-candidate, assume it may be part of a hand
    hand_candidates, hand_region_coordinates = get_hand_candidates(
            regions,
            final_candidate_labels,
            img_height,
            img_width,
            BORDER_OFFSET)
    progress_bar(100, 84)
    
    # Remove non-candidate regions from final mask
    remove_noncandidate_regions_from_mask(
            regions, 
            hand_candidates, 
            noartifacts_superpixel_mask)
    progress_bar(100, 90)

    extracted_hand, hand_label_mask = extract_hand(
            noborder_bin_image,
            noartifacts_superpixel_mask,
            hand_region_coordinates,
            original)
    progress_bar(100, 96)
  
    extracted_hand_alpha = add_alpha_channel(extracted_hand, hand_label_mask)
    progress_bar(100, 99)

    # Save hand
    cv2.imwrite(output_folder_path + "hand0.png", extracted_hand_alpha)
    
    progress_bar(100, 100)

def entry_point():
    if len(sys.argv) < 3:
        raise ValueError("Usage: %s INPUT_IMG OUTPUT_FOLDER" % sys.argv[0])

    input_img_path = sys.argv[1]
    output_folder_path = sys.argv[2]
    if not os.path.exists(input_img_path):
        raise ValueError("%s doesn't exist" % input_img_path)
    if os.path.exists(output_folder_path):
        if not os.path.isdir(output_folder_path):
            raise ValueError("%s is not a folder" % output_folder_path)
    if not output_folder_path.endswith(os.sep):
        output_folder_path += os.sep
    image_name = os.path.basename(input_img_path).split(".")[0]
    output_folder_path += image_name + os.sep
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    main(input_img_path, output_folder_path)

if __name__ == "__main__":
    entry_point()
