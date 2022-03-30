from .layers import Layer


class Colors(Layer):
    conv_color = "rgb:yellow,5;red,2.5;white,5"
    conv_relu_color = "rgb:yellow,5;red,5;white,5"
    pool_color = "rgb:red,1;black,0.3"
    unpool_color = "rgb:red,1;black,0.3"
    fc_color = "rgb:blue,5;red,2.5;white,5"
    fc_relu_color = "rgb:blue,5;red,5;white,5"
    softmax_color = "rgb:white,2;black,4"
    dense_color = "rgb:white,2;black,4"
    sum_color = "rgb:blue,5;green,15"

    def __init__(self):
        self.hidden_name = "colors"

    def text(self, depth_factor: float = 1.0, idx: int = None):
        return (
            "\\def\\ConvColor{{{0}}}\n"
            "\\def\\ConvReluColor{{{1}}}\n"
            "\\def\\PoolColor{{{2}}}\n"
            "\\def\\UnpoolColor{{{3}}}\n"
            "\\def\\FcColor{{{4}}}\n"
            "\\def\\FcReluColor{{{5}}}\n"
            "\\def\\SoftmaxColor{{{6}}}\n"
            "\\def\\DenseColor{{{7}}}\n"
            "\\def\\SumColor{{{8}}}".format(
                Colors.conv_color,
                Colors.conv_relu_color,
                Colors.pool_color,
                Colors.unpool_color,
                Colors.fc_color,
                Colors.fc_relu_color,
                Colors.softmax_color,
                Colors.dense_color,
                Colors.sum_color,
            )
        )

    @classmethod
    def Conv(cls, str: str):
        Colors.conv_color = str

    @classmethod
    def ConvRelu(cls, str: str):
        Colors.conv_relu_color = str

    @classmethod
    def Pool(cls, str: str):
        Colors.pool_color = str

    @classmethod
    def Unpool(cls, str: str):
        Colors.unpool_color = str

    @classmethod
    def Fc(cls, str: str):
        Colors.fc_color = str

    @classmethod
    def FcRelu(cls, str: str):
        Colors.fc_relu_color = str

    @classmethod
    def Softmax(cls, str: str):
        Colors.softmax_color = str

    @classmethod
    def Dense(cls, str: str):
        Colors.dense_color = str

    @classmethod
    def Sum(cls, str: str):
        Colors.sum_color = str
