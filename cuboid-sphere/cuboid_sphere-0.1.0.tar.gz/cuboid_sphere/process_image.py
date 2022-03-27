import cv2
import numpy as np
import math


def binarise_image(image, v1=128, v2=255):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.threshold(gray, v1, v2, cv2.THRESH_BINARY)[1]
    return binary


def get_shape_name(contour):
    """
    Check if contour is cuboid or rectangle
    """
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.01 * peri, True)

    if len(approx) > 4 and len(approx) <= 7:
        return "cuboid", approx.squeeze()
    if len(approx) == 4:
        return "rectangle", approx.squeeze()
    return "unknown", approx.squeeze()


def get_x_y_coordinates(contour, image, padding=15):
    """
    Returns xmin, ymin, xmax, ymax with added padding
    """
    height, width = image.shape[:2]

    contour = np.array(contour)
    xmin = np.min(contour[:, 1])
    ymin = np.min(contour[:, 0])
    xmax = np.max(contour[:, 1])
    ymax = np.max(contour[:, 0])
    xmin = max(0, xmin - padding)
    ymin = max(0, ymin - padding)
    xmax = min(height, xmax + padding)
    ymax = min(width, ymax + padding)

    return xmin, ymin, xmax, ymax


def binarise_until_find_rectangle(image, start=100, end=255):
    """
    Binarise image with range of threhsolds until found 4 sides of the rectangle
    """
    start_ranges = np.arange(start, end, 5)
    for start_n in start_ranges:
        binary = binarise_image(image, start_n, end)
        contours, _ = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = contours[0]
        shape_name, approx = get_shape_name(contour)

        if shape_name == "rectangle":
            return approx
            
        if not len(contours):
            return None
    return None


def get_rectangle_info(edges, image_org):
    """
    Indetiying cuboid and then extracting rectangle out from cuboid using:
    Edge detection -> N Lines to decide shape -> binarization -> extract rectangle
    """
    image = image_org.copy()
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rect_result = []
    for contour in contours:
        shape_name, approx = get_shape_name(contour)

        if shape_name == "cuboid": # if cuboid detected
            # Extracting rectangle from the cuboid
            rect_result.append({"shape": "cuboid", "contour": approx.tolist(), "pixel_area_convered": cv2.contourArea(approx)})

            # extract cuboid roi 
            xmin, ymin, xmax, ymax = get_x_y_coordinates(approx, image)
            cropped_rectangle = image[xmin:xmax, ymin:ymax]
            new_approx = binarise_until_find_rectangle(cropped_rectangle)

            if new_approx is not None: # if rectangle found
                new_approx = [[cnt[0] + ymin, cnt[1] + xmin] for cnt in new_approx]
                approx = np.array(new_approx, dtype=int)
                rect_result.append({"shape": "rectangle", "contour": approx.tolist(), "pixel_area_convered": cv2.contourArea(approx)})
                break

        elif shape_name == "rectangle": # if rectangle detected
            rect_result.append({"shape": "rectangle", "contour": approx.tolist(), "pixel_area_convered": cv2.contourArea(approx)})

    return rect_result


def get_circle_info(edges):
    """
    Identify circles using hough Circles after edge detection
    """
    circle_results = []
    circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, 2.5, 800)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            circle_results.append({"shape": "circle", "radius": float(r), "center": [int(x), int(y)], "area": float(math.pi * r * r)})

    return circle_results    


def get_edges(image):
    """
    Edge detection using Canny seperately for rectangle and circle with custom values
    """
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (3,3), 0)
    rect_edges = cv2.Canny(image=img_blur, threshold1=50, threshold2=200) # Canny Edge Detection
    circle_edges = cv2.Canny(image=img_blur, threshold1=1, threshold2=200) # Canny Edge Detection
    return rect_edges, circle_edges


def process_2d_image(image):
    """
    Identify cuboids, rectangles and circle and its corresponding pixel area covered

    Returns: type: Dict : Dictionary of shape, contour, pixel_area_convered
    """
    rect_edges, circle_edges = get_edges(image)
    rectangle_result = get_rectangle_info(rect_edges.copy(), image)
    circle_result    = get_circle_info(circle_edges.copy())
    final_result = rectangle_result + circle_result
            
    return final_result
