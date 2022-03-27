from cv2 import threshold
import h5py
import numpy as np
from sensor_msgs.msg import PointCloud
from geometry_msgs.msg import Point32
import numpy as np
import matplotlib.pyplot as plt

# Given
CX = 0.5
CY = 0.5


def display(img):
    plt.imshow(img)
    plt.show()


def new_disparity_to_pcl(disparity, fx, fy, cx, cy, baseline=0.54):
    height, width = disparity.shape[:2]
    # d = baseline * fx / disparity
    d = baseline * fx / (disparity + 1e-6)
    threshold = 10
    d = d * (d < threshold)

    x = np.arange(height).astype(np.float)
    y = np.arange(width).astype(np.float)
    x = (x - cx) / fx
    y = (y - cy) / fy

    X = -1 * np.multiply(d.T, x).T
    Y = -1 * np.multiply(d, y)

    d = d.flatten()
    depth = d[d!=0]
    X = (X.flatten())
    X = X[d!=0]
    Y = (Y.flatten())
    Y = Y[d!=0]
    step = 10

    pointcloud = PointCloud()
    pointcloud.header.frame_id = 'depth_frame'

    for i in range(0, len(depth), step):
        pointcloud.points.append(Point32(depth[i], Y[i], X[i]))
    
    return pointcloud



def disparity_to_pcl(disparity, fx, fy, cx, cy):
    """
    Convert disparity map to point cloud
    """
    # Get disparity map dimensions
    height, width = disparity.shape[:2]

    # Create point cloud
    pcl = PointCloud()
    pcl.header.frame_id = 'depth_frame'
    pcl.points = []

    # Convert disparity map to point cloud
    for y in range(height):
        for x in range(width):
            # Get disparity value
            d = disparity[y, x]

            # Skip invalid pixels
            if d == 0:
            # if d < 30:
                continue

            # Convert to 3D coordinates
            x3d = (x - cx) * d / fx
            y3d = (y - cy) * d / fy
            z3d = d

            # Add point to point cloud
            pcl.points.append(Point32(x3d, y3d, z3d))
            # pcl.points.append(Point32(z3d, y3d, x3d))
    
    return pcl


def save_pcl_to_ply(pcl, save_path):
    """
    Save point cloud to PLY file
    """
    # Create PLY file
    ply = open(save_path, 'w')

    # Write header
    ply.write('ply\n')
    ply.write('format ascii 1.0\n')
    ply.write('element vertex %d\n' % len(pcl.points))
    ply.write('property float x\n')
    ply.write('property float y\n')
    ply.write('property float z\n')
    ply.write('end_header\n')

    # Write point cloud
    for i in range(len(pcl.points)):
        ply.write('%f %f %f\n' % (pcl.points[i].x, pcl.points[i].y, pcl.points[i].z))

    # Close file
    ply.close()


def process_hdf5(filename, cx=CX, cy=CY, ply_path='pcl.ply'):
    with h5py.File(filename, "r") as f:
        depth_map = f['depth_map']
        intensity_map = f['intensity_map']
        fx = depth_map.attrs['horizontal_fov_deg']
        fy = depth_map.attrs['vertical_fov_deg']

        # point_cloud = disparity_to_pcl(intensity_map, fx, fy, cx, cy)
        # cx = 200
        # cy = 200
        # fx = 60
        # fy = 40
        intensity_map = np.array(intensity_map, np.uint8)
        # intensity_map[intensity_map == 0] = 10
        # point_cloud = new_disparity_to_pcl(intensity_map, fx, fy, cx, cy)
        point_cloud = disparity_to_pcl(intensity_map, fx, fy, cx, cy)
        
        import cv2
        cv2.imwrite('intensity.png', np.array(intensity_map))
        save_pcl_to_ply(point_cloud, ply_path)
    return ply_path


import cv2
import open3d
from open3d.visualization import draw_geometries
def process_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    fx = 200
    fy = 200
    cx = 213
    cy = 216

    

    # point_cloud = disparity_to_pcl(image, fx, fy, cx, cy)    
    point_cloud = new_disparity_to_pcl(image, fx, fy, cx, cy)
    save_pcl_to_ply(point_cloud, 'test.ply')

    cloud = open3d.io.read_point_cloud("test.ply") # Read the point cloud
    draw_geometries([cloud]) # Visualize the point cloud
    

if __name__ == '__main__':
    
    # filename = '/home/ben/personal/interview_assignment/lightcode_photonics/cuboid_sphere/depth_test.webp'
    # # filename = '/home/ben/Downloads/12.jpg'
    # process_image(filename)
    # exit()

    filename = "/home/ben/personal/interview_assignment/lightcode_photonics/cuboid_sphere/test_data/cuboid-sphere5.hdf5"
    ply_path = process_hdf5(filename)

    import open3d
    from open3d.visualization import draw_geometries

    cloud = open3d.io.read_point_cloud("pcl.ply") # Read the point cloud
    draw_geometries([cloud]) # Visualize the point cloud
