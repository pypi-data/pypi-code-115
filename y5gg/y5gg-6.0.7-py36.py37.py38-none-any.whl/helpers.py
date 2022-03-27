from pathlib import Path

from y5gg.models.yolo import Model
from y5gg.models.experimental import attempt_load
from y5gg.utils.general import set_logging, yolov5_in_syspath
from y5gg.utils.google_utils import attempt_download
from y5gg.utils.torch_utils import select_device
from y5gg.utils.torch_utils import torch


def load_model(model_path, device=None, autoshape=True, verbose=False):
    """
    Creates a specified YOLOv5 model

    Arguments:
        model_path (str): path of the model
        config_path (str): path of the config file
        device (str): select device that model will be loaded (cuda device, i.e. 0 or 0,1,2,3 or cpu)
        pretrained (bool): load pretrained weights into the model
        autoshape (bool): make model ready for inference
        verbose (bool): if False, yolov5 logs will be silent

    Returns:
        pytorch model

    (Adapted from y5gg.hubconf.create)
    """
    # set logging
    set_logging(verbose=verbose)

    # set device if not given
    if device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    device = select_device(device)

    attempt_download(model_path)  # download if not found locally
    with yolov5_in_syspath():
        #model = torch.load(model_path, map_location=torch.device(device))
        model = torch.load(model_path, map_location=device)
    if isinstance(model, dict):
        model = model["model"]  # load model
    hub_model = Model(model.yaml)  # create
    msd = model.state_dict()  # model state_dict
    csd = model.float().state_dict()  # checkpoint state_dict as FP32
    csd = {k: v for k, v in csd.items() if msd[k].shape == v.shape}  # filter
    hub_model.load_state_dict(csd, strict=False)  # load
    hub_model.names = model.names  # class names
    model = hub_model

    if autoshape:
        model = model.autoshape()

    return model.to(device)


class YOLOv5:
    def __init__(self, model_path, device=None, load_on_init=True):
        self.model_path = model_path
        self.device = device
        if load_on_init:
            Path(model_path).parents[0].mkdir(parents=True, exist_ok=True)
            self.model = load_model(model_path=model_path, device=device, autoshape=True)
        else:
            self.model = None

    def load_model(self):
        """
        Load yolov5 weight.
        """
        Path(self.model_path).parents[0].mkdir(parents=True, exist_ok=True)
        self.model = load_model(model_path=self.model_path, device=self.device, autoshape=True)

    def predict(self, image_list, size=640, augment=False):
        """
        Perform yolov5 prediction using loaded model weights.

        Returns results as a y5gg.models.common.Detections object.
        """
        assert self.model is not None, "before predict, you need to call .load_model()"
        results = self.model(imgs=image_list, size=size, augment=augment)
        return results

if __name__ == "__main__":
    model_path = "yolov5/weights/yolov5s.pt"
    device = "cuda"
    model = load_model(model_path=model_path, config_path=None, device=device)

    from PIL import Image
    imgs = [Image.open(x) for x in Path("yolov5/data/images").glob("*.jpg")]
    results = model(imgs)
