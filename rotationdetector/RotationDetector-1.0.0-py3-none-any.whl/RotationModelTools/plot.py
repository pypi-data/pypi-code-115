import math
import numpy as np
from RotationDetector.RotationModelTools.utils import xywh2xyxy, xywha2xyxyxyxy


def rescale_boxes(boxes, current_dim, original_shape):
    """ Rescales bounding boxes to the original shape """
    orig_h, orig_w = original_shape
    # The amount of padding that was added
    pad_x = max(orig_h - orig_w, 0) * (current_dim / max(original_shape))
    pad_y = max(orig_w - orig_h, 0) * (current_dim / max(original_shape))
    # Image height and width after padding is removed
    unpad_h = current_dim - pad_y
    unpad_w = current_dim - pad_x
    # Rescale bounding boxes to dimension of original image
    boxes[:, :4] = xywh2xyxy(boxes[:, :4])
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    x1 = ((x1 - pad_x // 2) / unpad_w) * orig_w
    y1 = ((y1 - pad_y // 2) / unpad_h) * orig_h
    x2 = ((x2 - pad_x // 2) / unpad_w) * orig_w
    y2 = ((y2 - pad_y // 2) / unpad_h) * orig_h
    boxes[:, 0] = (x1 + x2) / 2
    boxes[:, 1] = (y1 + y2) / 2
    boxes[:, 2] = (x2 - x1)
    boxes[:, 3] = (y2 - y1)
    return boxes


def get_color(c, x, max_val):
    colors = np.array([[1, 0, 1], [0, 0, 1], [0, 1, 1], [0, 1, 0], [1, 1, 0], [1, 0, 0]], dtype=np.float32)

    ratio = float(x) / max_val * 5
    i = int(math.floor(ratio))
    j = int(math.ceil(ratio))
    ratio = ratio - i
    r = (1 - ratio) * colors[i][c] + ratio * colors[j][c]
    return int(r * 255)

import os

def plot_boxes(img_path, boxes, class_names, img_size, color=None, conf = 0):
    import cv2 as cv
    img = np.array(cv.imread(img_path))

    boxes = rescale_boxes(boxes, img_size, img.shape[:2])
    boxes = np.array(boxes)
    if not (os.path.exists("output")):
        os.mkdir("output")
    txtPath = os.path.join("output", os.path.split(img_path)[-1].replace(".png", ".txt"))
    with open(txtPath,"w",encoding='utf-8') as file:
        for i in range(len(boxes)):
            box = boxes[i]
            if conf <= float(round(box[5] * box[6], 2)):
                x, y, w, h, theta = box[0], box[1], box[2], box[3], box[4]

                X1, Y1, X2, Y2, X3, Y3, X4, Y4 = xywha2xyxyxyxy(np.array([x, y, w, h, theta]))
                X1, Y1, X2, Y2, X3, Y3, X4, Y4 = int(X1), int(Y1), int(X2), int(Y2), int(X3), int(Y3), int(X4), int(Y4)

                bbox = np.int0([(X1, Y1), (X2, Y2), (X3, Y3), (X4, Y4)])
                cv.drawContours(img, [bbox], 0, (0, 255, 0), 2)


                if color:
                    rgb = color
                else:
                    rgb = (255, 0, 0)

                cls_id = np.squeeze(int(box[7]))
                classes = len(class_names)
                offset = cls_id * 123457 % classes
                red = get_color(2, offset, classes)
                green = get_color(1, offset, classes)
                blue = get_color(0, offset, classes)
                if color is None:
                    rgb = (red, green, blue)
                img = cv.putText(img, class_names[cls_id] + ":" + str(round(box[5] * box[6], 2)),
                                 (X1, Y1), cv.FONT_HERSHEY_SIMPLEX, 1, rgb, 1)
                # class_names[cls_id]为对应类别
                # 置信度为str(round(box[5] * box[6], 2))
                pixel_list = str(X1)+' '+str(Y1)+' '+str(X2)+' '+str(Y2)+' '+str(X3)+' ' +str(Y3)+' '+str(X4)+' '+str(Y4)
                line = class_names[cls_id] + ' ' + str(round(box[5] * box[6], 2)) + ':' + pixel_list + '\n'
                file.write(line)
    cv.imwrite(txtPath.replace("txt", "png"), img)


def load_class_names(namesfile : list):
    class_names = []
    for name in namesfile:
        class_names.append(name)
    return class_names
