import argparse
import os
import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt
from PIL import Image
from cuboid_sphere import models


# Copied and modified from https://github.com/Abhinandan11/depth-map  


class DepthMap:
    def __init__(self, model_path=None, height=228, width=304, channels=3, batch=1) -> None:
        self.height = height
        self.width = width
        self.channels = channels
        self.batch_size = batch
        self.model_path = model_path
        self._load_model()
    

    def _load_model(self):
        print("Loading Model...")
        # with tf.Session() as sess:
        self.sess = tf.Session()
        self.input_node = tf.placeholder(tf.float32, shape=(None, self.height, self.width, self.channels))
        self.net = models.ResNet50UpProj({'data': self.input_node}, self.batch_size, 1, False)
        self.saver = tf.train.Saver()
        self.saver.restore(self.sess, self.model_path)
    
    def convert_pil_img_gray_to_rgb(self, img):
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img

        
    def load_image(self, image_path):
        if isinstance(image_path, str):
            img = Image.open(image_path)
        else:
            img = Image.fromarray(image_path)
        img = self.convert_pil_img_gray_to_rgb(img)
        img = img.resize([self.width, self.height], Image.ANTIALIAS)
        img = np.array(img).astype('float32')
        img = np.expand_dims(np.asarray(img), axis = 0)
        return img
    

    def post_process(self, pred):
        pred = np.squeeze(pred)
        rmin = 0
        rmax = pred.max()
        pred = (pred - rmin) / (rmax - rmin) # normalise
        pred = np.absolute(pred - 1) # invert -> need disparity map
        return pred


    def predict(self, image):
        image_input = self.load_image(image)
        pred = self.sess.run(self.net.get_output(), feed_dict={self.input_node: image_input})
        pred = self.post_process(pred)
        return pred


if __name__ == '__main__':
    model_path = "/home/ben/personal/interview_assignment/lightcode_photonics/depth-map/models/NYU_FCRN.ckpt"
    image_path = "/home/ben/personal/interview_assignment/lightcode_photonics/cuboid_sphere/intensity.png"
    dm = DepthMap(model_path=model_path)

    r = dm.predict(image_path)
    import matplotlib.pyplot as plt
    def display(img):
        plt.imshow(img)
        plt.show()
    print(r.shape, r.max(), r.min())
    display(r)
    # print(r)
