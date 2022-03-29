import argparse
from collections import defaultdict

try:
    import cv2
except ImportError as e:
    print('OpenCV does not exist, camera disabled : {}'.format(e))

class KeyCallback(object):
    def __init__(self):
        self.kmap_ = {
                255 : lambda: False,
                ord('q') : lambda: True
                }
    def log(self, k):
        print(k)
        return False
    def update(self, kcb):
        self.kmap_.update(kcb)
    def __call__(self, k):
        k = (k & 0xff)
        if k not in self.kmap_:
            print('k', k)
            return False
        f = self.kmap_[k]
        return f()


def main():
    # handle arguments
    parser = argparse.ArgumentParser(description='OpenCV Camera')
    parser.add_argument('--dev', dest='dev', type=str,
            help='camera device', required=True)

    args = parser.parse_args()
    cam = cv2.VideoCapture(args.dev)
    kcb = KeyCallback()

    while True:
        ret, img = cam.read()
        if not ret:
            print('ret', ret)
            break
        cv2.imshow('img', img)
        k = cv2.waitKey(1)
        if kcb(k):
            break


if __name__ == '__main__':
    main()
