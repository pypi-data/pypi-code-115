from pathlib import Path

from y5facegg.models.yolo import Model
from y5facegg.models.experimental import attempt_load
from y5facegg.utils.general import y5face_in_syspath
from y5facegg.utils.torch_utils import select_device
from y5facegg.utils.detect_utils import detect_one
from y5facegg.utils.visualize_utils import visualize_detections
import torch

def load_model(model_path, device=None):
    """
    Creates a specified YOLOv5 model

    Arguments:
        model_path (str): path of the model
        device (str): select device that model will be loaded (cuda device, i.e. 0 or 0,1,2,3 or cpu)
    Returns:
        pytorch model
    """
#    # set device if not given
#    if device is None:
#        device = "cuda:0" if torch.cuda.is_available() else "cpu"
#    device = select_device(device)
    with y5face_in_syspath():
        #model = torch.load(model_path, map_location=torch.device(device))
        #model = torch.load(model_path, map_location=device)
        model = attempt_load(model_path, map_location=device)  # load FP32 model
    return model


class Y5FACE:
    def __init__(self, model_path, device=None, load_on_init=True):
        self.model_path = model_path
        # set device if not given
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#            device = "cuda:0" if torch.cuda.is_available() else "cpu"
#        device = select_device(device)
        self.device = device
        if load_on_init:
            Path(model_path).parents[0].mkdir(parents=True, exist_ok=True)
            self.model = load_model(model_path=self.model_path, device=self.device)
        else:
            self.model = None

    def load_model(self):
        """
        Load yolov5 weight.
        """
        Path(self.model_path).parents[0].mkdir(parents=True, exist_ok=True)
        self.model = load_model(model_path=self.model_path, device=self.device)

    def predict(self, bgr_image, size=640):
        """
        Perform yolov5 prediction using loaded model weights.
        """
        assert self.model is not None, "before predict, you need to call .load_model()"
        detections = detect_one(self.model, bgr_image, device=self.device, img_size=size)
        return detections

if __name__ == "__main__":
    model_path = 'weights/yolov5s-face.pt'
    model = Y5FACE(model_path)
    
    image_path = 'data/images/test.jpg'
    bgr_image = cv2.imread(image_path)
    
    detections = model.predict(bgr_image)
    
    res_img = visualize_one(bgr_image, detections)
    
    cv2.imwrite('result2.jpg', res_img)
