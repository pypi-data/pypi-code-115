from RotationDetector.RotationModelYolov4.utils import *

class Head(nn.Module):
    def __init__(self, output_ch,add_conv=True):
        super().__init__()
        self.conv1 = Conv(128, 256, 3, 1, 'leaky')
        self.conv2 = Conv(256, output_ch, 1, 1, 'linear', bn=False, bias=True)
        self.conv3 = Conv(128, 256, 1, 2, 'leaky')
        self.conv11 = Conv(256, 512, 1, 2, 'leaky')
        if add_conv:
            # x13在concat前进行多次卷积,分别为131
            # x6在concat前同样进行多次卷积,分别为131)
            self.add_P3_conv1 = Conv(256, 128, 3, 1, 'leaky')
            self.add_P3_conv2 = Conv(128, 256, 1, 1, 'leaky')

            self.add_P4_conv1 = Conv(512, 256, 3, 1, 'leaky')
            self.add_P4_conv2 = Conv(256, 512, 1, 1, 'leaky')
        # R -1 -16
        self.conv4 = Conv(512, 256, 1, 1, 'leaky')
        self.conv5 = Conv(256, 512, 3, 1, 'leaky')
        self.conv6 = Conv(512, 256, 1, 1, 'leaky')
        self.conv7 = Conv(256, 512, 3, 1, 'leaky')
        self.conv8 = Conv(512, 256, 1, 1, 'leaky')
        self.conv9 = Conv(256, 512, 3, 1, 'leaky')
        self.conv10 = Conv(512, output_ch, 1, 1, 'linear', bn=False, bias=True)
        # R -1 -37
        self.conv12 = Conv(1024, 512, 1, 1, 'leaky')
        self.conv13 = Conv(512, 1024, 3, 1, 'leaky')
        self.conv14 = Conv(1024, 512, 1, 1, 'leaky')
        self.conv15 = Conv(512, 1024, 3, 1, 'leaky')
        self.conv16 = Conv(1024, 512, 1, 1, 'leaky')
        self.conv17 = Conv(512, 1024, 3, 1, 'leaky')
        self.conv18 = Conv(1024, output_ch, 1, 1, 'linear', bn=False, bias=True)

    def forward(self, input1, input2, input3):
        # 3个输入，input1, input2, input3分别为多次卷积的x20,x13,x6
        # x20不用管，直接拼接
        x1 = self.conv1(input1)
        x2 = self.conv2(x1)
        # x13在concat前进行多次卷积
        x3 = self.conv3(input1)
        x3 = self.add_P3_conv1(x3)
        x3 = self.add_P3_conv2(x3)

        x3 = torch.cat([x3, input2], dim=1)
        x4 = self.conv4(x3)
        x5 = self.conv5(x4)
        x6 = self.conv6(x5)
        x7 = self.conv7(x6)
        x8 = self.conv8(x7)
        x9 = self.conv9(x8)
        x10 = self.conv10(x9)
        # # x13在concat前进行多次卷积
        x11 = self.conv11(x8)
        x11 = self.add_P4_conv1(x11)
        x11 = self.add_P4_conv2(x11)

        x11 = torch.cat([x11, input3], dim=1)
        x12 = self.conv12(x11)
        x13 = self.conv13(x12)
        x14 = self.conv14(x13)
        x15 = self.conv15(x14)
        x16 = self.conv16(x15)
        x17 = self.conv17(x16)
        x18 = self.conv18(x17)

        return x2, x10, x18
