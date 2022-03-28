
import torch
from RotationDetector.RotationModelYolov4 import RotationModel
# 注意，这里直接转化会出现问题，因为torch.onnx.export时，模型的返回值中不能存在int类型
# 因此，需要删掉yoloLayer和model返回值中的loss
modelpath = "weights/weight.pth"
onnxpath = modelpath.replace(".pth",".onnx")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
pretrained_dict = torch.load(modelpath, map_location=torch.device('cpu'))
FloatTensor = torch.cuda.FloatTensor if torch.cuda.is_available() else torch.FloatTensor
model = RotationModel(n_classes=3)
model = model.to(device)
model.load_state_dict(pretrained_dict)
model.eval()

inputshape = (1,3,608,608)
example = torch.randn(inputshape).cuda()
torch.onnx.export(model, example, onnxpath, verbose=1,opset_version=11)