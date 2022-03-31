from pydicom.pixel_data_handlers.numpy_handler import get_pixeldata
from pydicom.pixel_data_handlers import apply_color_lut, convert_color_space
import pydicom as dicom
import numpy as np

import os


def get_image(ds, frame_num=0):
    num_frames = 1
    if 'NumberOfFrames' in ds.dir():
        num_frames = ds.NumberOfFrames
        # print('Num Frames:', num_frames)
    width = ds.Columns
    height = ds.Rows
    spp = ds.SamplesPerPixel
    phi = ds.PhotometricInterpretation
    bpp = ds.BitsAllocated
    pr = ds.PixelRepresentation
    pc = 0
    if "PlanarConfiguration" in ds.dir():
        pc = ds.PlanarConfiguration
    try:
        rgb = None
        image = get_pixeldata(ds)
        if num_frames > 1:
            rgb = image[frame_num]
        else:
            rgb = image
        if len(rgb.shape) == 1:
            if spp == 1:
                rgb = rgb.reshape(height, width)
            else:
                rgb = rgb.reshape(height, width, spp)
        if bpp != 8:
            img_min = np.amin(rgb)
            img_max = np.amax(rgb)
            img_range = max(img_max - img_min, 1)
            tmp = ((rgb - img_min)/img_range).astype('float32')
            rgb = (tmp*255).astype('uint8')
        else:
            rgb = rgb.astype('uint8')
    except Exception as e:
        print('Exception happened in read_image.py')
        print(e)
        image = None
        if num_frames > 1:
            image = ds.pixel_array[frame_num]
        else:
            image = ds.pixel_array
        if len(image.shape) == 1:
            image = image.reshape(height, width)
        tmp = None
        if phi == 'PALETTE COLOR':
            tmp = apply_color_lut(image, ds)
        elif phi == 'YBR_FULL' or phi == 'YBR_FULL_422':
            tmp = convert_color_space(image, phi, 'RGB')
            pc = 0
            # print("Force pc = 0 after color_conversion")
        else:
            tmp = image
        if pc == 1 and spp > 1:
            tmp1 = np.empty(spp, height, width)
            for i in range(spp):
                tmp1[i] = tmp[i::spp]
            tmp = tmp1
        if pr == 1:
            mid_val = pow(2, (bpp-1))
            tmp = tmp.astype(np.int32)
            tmp = tmp + mid_val
        if bpp != 8 or tmp.dtype != np.uint8:
            img_min = np.amin(tmp)
            img_max = np.amax(tmp)
            img_range = max(img_max - img_min, 1)
            tmp = ((tmp - img_min)/img_range).astype('float32')
            rgb = (tmp*255).astype('uint8')
        else:
            rgb = tmp.astype('uint8')
        #if spp == 1:
        #    tmp = rgb
        #    rgb = np.asarray(np.dstack((tmp, tmp, tmp)), dtype=np.uint8)
    return rgb


def read_dicom_image(image_path, frame_num=0):
    try:
        ds = dicom.dcmread(image_path)
        image = get_image(ds, frame_num)
        return image
    except:
        print('Failed with exception for image: ' + image_path)
        return []