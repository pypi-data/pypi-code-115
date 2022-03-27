import requests
import cv2
import numpy as np
import h5py
import matplotlib.pyplot as plt


LOCAL_HOST = 'http://localhost'
DEFAULT_PORT = '6500'


def display(img, title_name="Image"):
    plt.cla()
    plt.clf()
    plt.close()

    plt.title(title_name)
    plt.imshow(img)
    plt.show()


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


def call_3d(file_path, X=0.5, Y=0.5, Z=1, scale=2.5, ip=LOCAL_HOST, port=DEFAULT_PORT):
    if not ip.startswith('http'):
        ip = f'http://{ip}'
        
    url = f'{ip}:{port}/hdf5'
    response = requests.post(url, files={'in_file': open(file_path, 'rb')}, data={'X': X, 'Y': Y, 'Z': Z, 'scale': scale})
    response = response.json()
    return response


def call_2d(image_path, ip=LOCAL_HOST, port=DEFAULT_PORT):
    if not ip.startswith('http'):
        ip = f'http://{ip}'
    url = f'{ip}:{port}/image'
    response = requests.post(url, files={'in_file': open(image_path, 'rb')})
    response = response.json()
    return response


def save_point_cloud(points, save_path="./point_cloud.hdf5"):
    """
    Save point cloud to HDF5 file
    """
    # Create HDF5 file
    hdf5 = h5py.File(save_path, 'w')

    # Create datasets
    hdf5.create_dataset('points', data=points)
    # hdf5.create_dataset('colors', data=(128, 128, 128))

    # Close file
    hdf5.close()
    print("Point cloud saved to: ", save_path)


def display_3d_result(hdf5_path, response):
    print("*"*40 + " 3D " + "*"*40)
    with h5py.File(hdf5_path, "r") as f:
        intesity_image = f['intensity_map']
        intesity_image = np.array(intesity_image) / 255

    point_cloud = response['point_cloud']
    disparity_map = response['disparity_map']
    disparity_map = np.array(disparity_map)

    results = response['results']
    print("#"*25 + " Results " + "#"*25)
    result_string = []
    for r in results:
        result_string.append(f"Shape: {r['shape']} | Surface Area: : {str(r['surface_area'])[:6]} | Volume: {str(r['volume'])[:7]} | Centroid: {r['centroid']}")
    result_string = "\n".join(result_string)
    print(result_string)
    print("#"*25 + " Disparity Map " + "#"*25)


    fig = plt.figure(figsize=(12, 6))
    fig.add_subplot(1, 2, 1)
    plt.imshow(intesity_image)
    plt.axis('off')
    plt.title("Intensity: Given")

    fig.add_subplot(1, 2, 2)
    plt.imshow(disparity_map)
    plt.axis('off')
    plt.title("Disparity: Dervied")
    
    fig.suptitle(f"Disparity Map X=0.5, Y=0.5, Z=1\n{result_string}")
    plt.show()

    # display(combined, f"Disparity Map X=0.5, Y=0.5, Z=1\n{result_string}")

    # Disable view of Point cloud as it disrupts Matplotlib display 
    # from open3d.visualization import draw_geometries
    # save_pcl_to_ply(point_cloud, 'temp.ply')
    # cloud = open3d.io.read_point_cloud("temp.ply") # Read the point cloud
    # draw_geometries([cloud], zoom=0.55999999999999983,
    #                               front=[ -0.55895911264221199, -0.72506512574529358, -0.40229997989335364 ],
    #                               lookat=[ 188.21250000000001, 224.1875, 128.0 ],
    #                               up=[ 0.73940658793245073, -0.65542510880077387, 0.15393448111318342]) # Visualize the point cloud

    print("*"*84)
    print()


def display_2d_result(image_path, response):
    print("*"*40 + " 2D " + "*"*40)
    image = cv2.imread(image_path)
    result_string = []
    for r in response:
            if r['shape'] == "circle":
                radius = int(r["radius"])
                center = r["center"]
                cv2.circle(image, (center[0], center[1]), radius, (255, 0, 255), 4)
                result_string.append(f"Shape: {r['shape']}    | Pixel Area: : {r['area']} | Radius: {r['radius']} | center: {r['center']}")
            
            elif r['shape'] == "rectangle":
                cv2.drawContours(image, [np.array(r['contour'])], -1, (0, 255, 0), 2)
                result_string.append(f"Shape: {r['shape']} | Pixel Area: : {r['pixel_area_convered']} | Contour: {r['contour'][:3]}....")

            elif r['shape'] == "cuboid":
                cv2.drawContours(image, [np.array(r['contour'])], -1, (255, 0, 0), 2)
                result_string.append(f"Shape: {r['shape']}    | Pixel Area: : {r['pixel_area_convered']} | Contour: {r['contour'][:3]}....")
    result_string = "\n".join(result_string)
    print(result_string)
    display(image, f"2D Edge Detection\n{result_string}")
    del image
    print("*"*84)

    
