# -*-coding: utf-8 -*-

import os, sys

sys.path.append(os.getcwd())
import onnxruntime
import torch
import time
import argparse


from torch.utils.data import DataLoader
from RotationDetector.RotationModelTools import load_class_names, plot_boxes, post_process, ImageDataset

def detectOnOnnx():
    pass

class ONNXModel():
    def __init__(self, onnx_path):
        """
        :param onnx_path:
        """
        self.onnx_session = onnxruntime.InferenceSession(onnx_path)
        self.input_name = self.get_input_name(self.onnx_session)
        self.output_name = self.get_output_name(self.onnx_session)
        print("input_name:{}".format(self.input_name))
        print("output_name:{}".format(self.output_name))

    def get_output_name(self, onnx_session):
        """
        output_name = onnx_session.get_outputs()[0].name
        :param onnx_session:
        :return:
        """
        output_name = []
        for node in onnx_session.get_outputs():
            output_name.append(node.name)
        return output_name

    def get_input_name(self, onnx_session):
        """
        input_name = onnx_session.get_inputs()[0].name
        :param onnx_session:
        :return:
        """
        input_name = []
        for node in onnx_session.get_inputs():
            input_name.append(node.name)
        return input_name

    def get_input_feed(self, input_name, image_numpy):
        """
        input_feed={self.input_name: image_numpy}
        :param input_name:
        :param image_numpy:
        :return:
        """
        input_feed = {}
        for name in input_name:
            input_feed[name] = image_numpy
        return input_feed

    def forward(self, image_numpy):
        '''
        # image_numpy = image.transpose(2, 0, 1)
        # image_numpy = image_numpy[np.newaxis, :]
        # onnx_session.run([output_name], {input_name: x})
        # :param image_numpy:
        # :return:
        '''
        # 输入数据的类型必须与模型一致,以下三种写法都是可以的
        # scores, boxes = self.onnx_session.run(None, {self.input_name: image_numpy})
        # scores, boxes = self.onnx_session.run(self.output_name, input_feed={self.input_name: iimage_numpy})
        input_feed = self.get_input_feed(self.input_name, image_numpy)
        scores = self.onnx_session.run(self.output_name, input_feed=input_feed)
        return scores


def to_numpy(tensor):
    print(tensor.device)
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_folder", type=str, default="data/detect", help="path to dataset")
    parser.add_argument("--weights_path", type=str, default="weights/yolov4_train_5.onnx", help="path to weights file")
    parser.add_argument("--class_path", type=str, default="data/coco.names", help="path to class label file")
    parser.add_argument("--conf_thres", type=float, default=0.85, help="object confidence threshold")
    parser.add_argument("--nms_thres", type=float, default=0.3, help="iou thresshold for non-maximum suppression")
    parser.add_argument("--batch_size", type=int, default=5, help="size of the batches")
    parser.add_argument("--img_size", type=int, default=608, help="size of each image dimension")
    args = parser.parse_args()
    time_start1 = time.time()
    rnet1 = ONNXModel(args.weights_path)
    time_end2 = time.time()
    print('load model cost', time_end2 - time_start1)
    class_names = load_class_names(args.class_path)
    dataset = ImageDataset(args.image_folder, img_size=args.img_size)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)
    boxes = []
    imgs = []
    start = time.time()
    for img_path, img in dataloader:
        with torch.no_grad():
            temp = time.time()
            output, _ = rnet1.forward(to_numpy(img))  # batch=1 -> [1, n, n], batch=3 -> [3, n, n]
            temp1 = time.time()
            box = post_process(torch.tensor(output), args.conf_thres, args.nms_thres)
            temp2 = time.time()
            boxes.extend(box)
            print('-----------------------------------')
            num = 0
            for b in box:
                num += len(b)
            print("{}-> {} objects found".format(img_path, num))
            print("Inference time : ", round(temp1 - temp, 5))
            print("Post-processing time : ", round(temp2 - temp1, 5))
            print('-----------------------------------')

        imgs.extend(img_path)

    for i, (img_path, box) in enumerate(zip(imgs, boxes)):
        plot_boxes(img_path, box, class_names, args.img_size)

    end = time.time()

    print('-----------------------------------')
    print("Total detecting time : ", round(end - start, 5))
    print('-----------------------------------')
