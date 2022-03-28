
import time
import random
import numpy as np

import torch
from torch.autograd import Variable

from RotationDetector.RotationModelTools import split_data, CosineAnnealingWarmupRestarts
from RotationDetector.Config import Config
from RotationDetector import RotationModel

def weights_init_normal(m):
    if isinstance(m, torch.nn.Conv2d):
        torch.nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif isinstance(m, torch.nn.BatchNorm2d):
        torch.nn.init.normal_(m.weight.data, 1.0, 0.02)
        torch.nn.init.constant_(m.bias.data, 0.0)


def init():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


config = Config()
config.setTrainFloder(r"D:\PycharmProjects\LBKProject\RotationDetector\trainData")
config.setPreTrainedWeightPath(None)
config.setTrainWeightPath("train.pth")
config.setNumberClasses(4)

def Train(config: Config):
    '''
    函数功能：进行模型训练
    Args:
        config: 配置类，必须的四个函数：数据文件夹，预训练模型，训练完模型的保存地址，类别
        建议通过set进行，例如：
        config = Config()
        config.setTrainFloder(r"D:\PycharmProjects\LBKProject\RotationDetector\trainData")
        config.setPreTrainedWeightPath(None)
        config.setTrainWeightPath("train.pth")
        config.setNumberClasses(4)


    Returns:训练的损失列表
    '''

    # 初始化工作
    init()
    device = torch.device('cuda')

    model = RotationModel(n_classes=config.numClasses)
    model = model.to(device)
    model_dict = model.state_dict()

    # 如果存在预训练文件
    if config.weightsPreTrainedPath != None:
        pretrained_dict = torch.load(config.weightsPreTrainedPath)
        pretrained_dict = {k: v for i, (k, v) in enumerate(pretrained_dict.items()) if i < 552}
        model_dict.update(pretrained_dict)

    model.apply(weights_init_normal)
    model.load_state_dict(model_dict)

    # 整理数据
    _, train_dataloader = split_data(config.trainFloder, config.image_size, config.batch_size)
    num_iters_per_epoch = len(train_dataloader)
    scheduler_iters = round(config.epochs * len(train_dataloader) / config.subdivisions)
    total_step = num_iters_per_epoch * config.epochs

    # 优化器
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    scheduler = CosineAnnealingWarmupRestarts(optimizer,
                                              first_cycle_steps=scheduler_iters,
                                              cycle_mult=1.0,
                                              max_lr=0.0001,
                                              min_lr=0,
                                              warmup_steps=round(scheduler_iters * 0.1),
                                              gamma=1.0)
    # 数据保存
    loss_plot = []
    for count,epoch in enumerate(range(config.epochs)):
        total_loss = 0.0
        start_time = time.time()
        print("\n---- [Epoch %d/%d] ----\n" % (epoch + 1, config.epochs))
        model.train()
        for batch, (_, imgs, targets) in enumerate(train_dataloader):
            global_step = num_iters_per_epoch * epoch + batch + 1
            imgs = Variable(imgs.to(device), requires_grad=True)
            targets = Variable(targets.to(device), requires_grad=False)
            outputs, loss = model(imgs, targets)
            loss.backward()
            total_loss += loss.item()

            if global_step % config.subdivisions == 0:
                optimizer.step()
                optimizer.zero_grad()
                scheduler.step()

            # ---------------------
            # -      logging      -
            # ---------------------
            tensorboard_log = []
            loss_table_name = ["Step: %d/%d" % (global_step, total_step),
                               "loss", "reg_loss", "conf_loss", "cls_loss"]
            loss_table = [loss_table_name]

            temp = ["YoloLayer1"]
            for name, metric in model.yolo1.metrics.items():
                if name in loss_table_name:
                    temp.append(metric)
                tensorboard_log += [(f"{name}_1", metric)]
            loss_table.append(temp)

            temp = ["YoloLayer2"]
            for name, metric in model.yolo2.metrics.items():
                if name in loss_table_name:
                    temp.append(metric)
                tensorboard_log += [(f"{name}_2", metric)]
            loss_table.append(temp)

            temp = ["YoloLayer3"]
            for name, metric in model.yolo3.metrics.items():
                if name in loss_table_name:
                    temp.append(metric)
                tensorboard_log += [(f"{name}_3", metric)]
            print(loss_table)
            loss_table.append(temp)
            loss_plot.append(loss_table)

        print("Total Loss: %f, Runtime %f" % (total_loss, time.time() - start_time))
    torch.save(model.state_dict(), config.TrainWeightPath)
    return np.array(loss_plot)
