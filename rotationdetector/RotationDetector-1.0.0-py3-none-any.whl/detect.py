import torch
import time
from torch.utils.data import DataLoader

from RotationDetector import RotationModel
from RotationDetector.RotationModelTools import plot_boxes, post_process, ImageDataset
from RotationDetector.Config import DectctConfig


dectctConfig = DectctConfig()
dectctConfig.setWeights_path(r"D:\PycharmProjects\LBKProject\RotationDetector-5720CrackAndOldCrack.pth")
dectctConfig.setDetectFile(r"D:\PycharmProjects\LBKProject\RotationDetector\data\detectData")
dectctConfig.setNumClasses(4)
dectctConfig.setClassName(['Scratch', 'Defeat', 'Crack', 'CrackOld'])


def Detect(dectctConfig : DectctConfig):
    device = torch.device('cuda')
    pretrained_dict = torch.load(dectctConfig.weights_path, map_location=torch.device('cpu'))
    model = RotationModel(n_classes=dectctConfig.NumClasses)
    model = model.to(device)
    model.load_state_dict(pretrained_dict)
    return model.eval()



if __name__ == "__main__":
    device = torch.device('cuda')
    model = Detect(dectctConfig)

    dataset = ImageDataset(dectctConfig.detectFile, imgSize=dectctConfig.imgSize)
    dataloader = DataLoader(dataset, batch_size=dectctConfig.batchSize, shuffle=False)

    boxes = []
    imgs = []
    start = time.time()
    for img_path, img in dataloader:
        img = torch.autograd.Variable(img.type(torch.cuda.FloatTensor))
        with torch.no_grad():
            temp = time.time()
            output, _ = model(img)  # batch=1 -> [1, n, n], batch=3 -> [3, n, n]
            temp1 = time.time()
            box = post_process.post_process(output.cpu(), dectctConfig.confThres, dectctConfig.numThres)
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
        plot_boxes(img_path, box, dectctConfig.className, dectctConfig.imgSize, color=None, conf=dectctConfig.confThres)

    end = time.time()

    print('-----------------------------------')
    print("Total detecting time : ", round(end - start, 5))
    print('-----------------------------------')
