import h5py
import numpy as np
import matplotlib.pyplot as plt
from cuboid_sphere.model_process import DepthMap
from cuboid_sphere.process_image import process_2d_image
import cv2
import os

# Given
CX = 0.5
CY = 0.5


docker_dir = "/cuboid_sphere/cuboid_sphere/models"
# Inside docker 
if os.path.exists(docker_dir):
    model_path = os.path.join(docker_dir, 'NYU_FCRN.ckpt')
# testing directory
else:
    model_path = "/home/ben/personal/interview_assignment/lightcode_photonics/depth-map/models/NYU_FCRN.ckpt"

depthmap_model = DepthMap(model_path=model_path)


def display(img):
    plt.imshow(img, cmap='gray')
    plt.show()


def disparity_to_pcl(disparity, fx, fy, cx, cy):
    """
    Convert disparity map to point cloud
    """
    height, width = disparity.shape[:2]
    points = []

    # Convert disparity map to point cloud
    for y in range(height):
        for x in range(width):
            d = disparity[y, x]
            # Skip invalid pixels
            if d == 0:
                continue

            # Convert to 3D coordinates
            x3d = (x - cx) * d / fx
            y3d = (y - cy) * d / fy
            z3d = d

            # Add point to point cloud
            points.append([x3d, y3d, z3d])
    points = np.array(points).tolist()
    
    return points


def save_pcl_to_ply(points, save_path):
    """
    Save point cloud to PLY file
    """
    # Create PLY file
    ply = open(save_path, 'w')

    # Write header
    ply.write('ply\n')
    ply.write('format ascii 1.0\n')
    ply.write('element vertex %d\n' % len(points))
    ply.write('property float x\n')
    ply.write('property float y\n')
    ply.write('property float z\n')
    ply.write('end_header\n')

    # Write point cloud
    for i in range(len(points)):
        ply.write('%f %f %f\n' % (points[i][0], points[i][1], points[i][2]))

    # Close file
    ply.close()


def scale_image(image, scale=2.5, upscale=True, original_shape=None):
    if original_shape:
        return cv2.resize(image, (original_shape[1], original_shape[0]))
    elif upscale:
        return cv2.resize(image, (int(image.shape[1]*scale), int(image.shape[0]*scale)), interpolation=cv2.INTER_NEAREST)
    else:
        return cv2.resize(image, (int(image.shape[1]/scale), int(image.shape[0]/scale)), interpolation=cv2.INTER_NEAREST)


def mask_circle_and_polygon(image, shape_results):
    new_image = np.zeros(image.shape, np.float)
    
    for r in shape_results:
        if r['shape'] == "circle":
            center = r['center']
            radius = r['radius']
            # fill cricle with white
            cv2.circle(new_image, center, radius, (1.0, 1.0, 1.0), -1)
        else:
            contour = np.array(r['contour'])
            cv2.fillPoly(new_image, pts=[contour], color=(1.0, 1.0, 1.0))
    
    image = image * new_image
    return image


def downscale_results_coordinates(results, scale):
    new_results = []
    for r in results:
        if r.get('contour'):
            new_contour = []
            for c in r['contour']:
                new_contour.append([int(c[0]/scale), int(c[1]/scale)])
            r['contour'] = new_contour
        
        if r.get('center'):
            r['center'] = [int(r['center'][0]/scale), int(r['center'][1]/scale)]
        
        if r.get('radius'):
            r['radius'] = int(r['radius']/scale)
        
        new_results.append(r)
    return new_results


def process_sphere(disparity_map, radius, center, X, Y, Z):
    """
    Process sphere information and return the surface_area, volume and centroid on the XYZ coordinates space
    """
    new_image = np.zeros(disparity_map.shape, np.float)
    cv2.circle(new_image, center, radius, (1.0, 1.0, 1.0), -1)

    # depth_of_circle_center = disparity_map[center[1], center[0]]
    depth_of_circle_top = disparity_map[center[1]-radius, center[0]]

    # Normalizing with X, Y and Z
    height, width = disparity_map.shape[:2]
    l = height if height > width else width
    L = Y if l == height else X
    new_radius = (radius / l) * L 

    surface_area = 4 * np.pi * new_radius * new_radius
    volume = 4/3 * np.pi * new_radius * new_radius * new_radius
    centroid =  [((center[0] / width) * X) , ((center[1] / height) * Y), depth_of_circle_top]

    return surface_area, volume, centroid


def get_top_left_contour(contour):
    min_x = min(contour, key=lambda x: x[0])[0]
    min_y = min(contour, key=lambda x: x[1])[1]
    return [min_x, min_y]


def get_bottom_right_contour(contour):
    max_x = max(contour, key=lambda x: x[0])[0]
    max_y = max(contour, key=lambda x: x[1])[1]
    return [max_x, max_y]


def process_cuboid(disparity_map, results, X, Y, Z):
    """
    Process cuboid and rectangle information to return surface area, volume, centroid on the XYZ coordinates space
    """
    rectangle_data = None
    cuboid_data = None
    for r in results:
        if r['shape'] == "rectangle":
            rectangle_data = r
        elif r['shape'] == "cuboid":
            cuboid_data = r
    
    # get calibrated Lenght and height from the rectangle
    rect_contours = np.array(rectangle_data['contour'])
    top_left_contour = get_top_left_contour(rect_contours)
    bottom_right_contour = get_bottom_right_contour(rect_contours)

    length = bottom_right_contour[0] - top_left_contour[0]
    height = bottom_right_contour[1] - top_left_contour[1]

    depth_distance = np.abs(disparity_map[bottom_right_contour[1], bottom_right_contour[0]] - disparity_map[top_left_contour[1], top_left_contour[0]])

    calibrated_length = length + (length * (depth_distance))
    calibrated_height = height + (height * (depth_distance))

    # get calibrated cuboid width from cuboid
    cuboid_contours = np.array(cuboid_data['contour'])

    # 1.5 is a magic number, it is the ratio between the width of the cuboid and the length of the cuboid, 
    # :) assumptions taken after seeing 10 different examples  to save time
    calibrated_width = (calibrated_length if calibrated_length > calibrated_height else calibrated_height) / 1.5 

    # normalize with respect to given X, Y and Z
    calibrated_length = (calibrated_length / disparity_map.shape[1]) * X
    calibrated_height = (calibrated_height / disparity_map.shape[0]) * Y 
    calibrated_width  = (calibrated_width / disparity_map.shape[1]) * Z

    surface_area = (2 * calibrated_length * calibrated_width + 2 * calibrated_length *  calibrated_height + 2 * calibrated_height * calibrated_width)
    volume = calibrated_length * calibrated_height * calibrated_width
    centroid = [((top_left_contour[0] / disparity_map.shape[1]) * X) , ((top_left_contour[1] / disparity_map.shape[0]) * Y), disparity_map[top_left_contour[1], top_left_contour[0]]]
    return surface_area, volume, centroid


def process_hdf5(filename, cx=CX, cy=CY, X=0.5, Y=0.5, Z=1, scale=2.5):
    """
    Processes the given hdf5 file and process shapes information and returns the results in a dictionary
    filename: path to the hdf5 file
    X,Y,Z: are the coordinates of a 3D point in the world coordinates space, which is given .5, .5, 1
    scale: For upscaling or downscaling image.
    """
    with h5py.File(filename, "r") as f:
        depth_map = f['depth_map'] # Values mostly Nan, not usable for 3D reconstruction
        intensity_map = f['intensity_map']
        fx = depth_map.attrs['horizontal_fov_deg']
        fy = depth_map.attrs['vertical_fov_deg']

        intensity_map = np.array(intensity_map, np.uint8)
        point_cloud = disparity_to_pcl(intensity_map, fx, fy, cx, cy)

        # Upscaling image to identify circle and rectangle shapes 
        # Does not identify the shapes well if not upscaled
        upscaled_image = scale_image(intensity_map, scale=scale, upscale=True)
        upscaled_image = cv2.cvtColor(upscaled_image, cv2.COLOR_GRAY2RGB)
        shape_2d_results = process_2d_image(upscaled_image)
        shape_2d_results = downscale_results_coordinates(shape_2d_results, scale)
        original_image = scale_image(upscaled_image, scale=scale, upscale=False)

        disparity_map = depthmap_model.predict(original_image)
        disparity_map = scale_image(disparity_map, original_shape=original_image.shape)
        
        disparity_map = mask_circle_and_polygon(disparity_map, shape_2d_results)
        
        # calculate surface area, volume and centroid of the shapes
        final_results = []
        cuboid_and_rect_result = []
        for r in shape_2d_results:
            if r['shape'] == "circle":
                center = r['center']
                radius = r['radius']
                surface_area, volume, centroid = process_sphere(disparity_map, radius, center, X, Y, Z)
                final_results.append({'shape': 'circle', 'surface_area': surface_area, 'volume': volume, 'centroid': centroid})
                
            else:
                cuboid_and_rect_result.append(r)
                
        surface_area, volume, centroid = process_cuboid(disparity_map, cuboid_and_rect_result, X, Y, Z)
        final_results.append({'shape': 'cuboid', 'surface_area': surface_area, 'volume': volume, 'centroid': centroid})
    
    return final_results, point_cloud, disparity_map.tolist()
