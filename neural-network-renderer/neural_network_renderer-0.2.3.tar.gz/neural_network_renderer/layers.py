from math import sqrt


class Layer:
    def __init__(self, name: str):
        self.hidden_name = name

    @property
    def name(self):
        return self.hidden_name

    def text(self, depth_factor: float = 1.0, idx: int = None):
        return


class Head(Layer):
    def __init__(self, projectpath: str):
        self.path = projectpath
        self.hidden_name = "head"

    def text(self, depth_factor: float = 1.0, idx: int = None):
        text = r"""
        \documentclass[border=8pt, multi, tikz]{standalone} 
        \usepackage{import}
        \usepackage{graphicx}
        \usepackage[export]{adjustbox}
        \usetikzlibrary{positioning}
        \usetikzlibrary{3d}
        \usepackage{etoolbox}% provides \preto

        \usetikzlibrary{quotes,arrows.meta}
        \usetikzlibrary{positioning}

        \def\edgecolor{rgb:blue,5;red,5;green,5;black,3}
        \newcommand{\midarrow}{\tikz \draw[-Stealth,line width =0.4mm,draw=\edgecolor] (-0.3,0) -- ++(0.3,0);}

        \usepackage{Ball}
        \usepackage{Box}
        \usepackage{RightBandedBox}
        """

        return text


class Begin(Layer):
    def __init__(self):
        self.hidden_name = "begin"

    def text(self, depth_factor: float = 1.0, idx: int = None):
        return r"""
        \newcommand{\copymidarrow}{\tikz \draw[-Stealth,line width=0.8mm,draw={rgb:blue,4;red,1;green,1;black,3}] (-0.3,0) -- ++(0.3,0);}

        \begin{document}
        \begin{tikzpicture}
        \tikzstyle{connection}=[ultra thick,every node/.style={sloped,allow upside down},draw=\edgecolor]
        \tikzstyle{copyconnection}=[ultra thick,every node/.style={sloped,allow upside down},draw={rgb:blue,4;red,1;green,1;black,3},opacity=0.7]
        """


class Input(Layer):
    def __init__(self, pathfile, shape: list[int], to="(0,0,0)", name="temp"):
        self.hidden_name = name
        self.pathfile = pathfile
        self.to = to
        self.width = shape[0]
        self.height = shape[1]

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \node[canvas is zy plane at x=0] (NAME) at TO 
        {\scalebox{-1}[1]{\includegraphics[width=WIDTHem, height=HEIGHTem, frame] {PATHFILE}}};
        """
        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(self.width / sqrt(3)))
        base_text = base_text.replace("HEIGHT", str(self.height / sqrt(3)))
        base_text = base_text.replace("PATHFILE", self.pathfile)

        return base_text


class Conv(Layer):
    def __init__(
        self,
        s_filter=256,
        n_filter=64,
        name: str = None,
        offset="(0,0,0)",
        to=None,
        opacity=0.9,
        caption=" ",
    ):
        self.hidden_name = name
        self.s_filter = s_filter
        self.n_filter = n_filter
        self.offset = offset
        self.to = to
        self.width = self.s_filter
        self.height = self.s_filter
        self.depth = n_filter
        self.opacity = opacity
        self.caption = caption

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Box={
                name=NAME, caption=CAPTION, xlabel={{N_FILTER, }}, zlabel=S_FILTER, opacity=OPACTIY, fill=\ConvColor, height=HEIGHT, width=WIDTH, depth=DEPTH
            }
        };
        """
        if not self.name:
            self.hidden_name = f"conv_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("CAPTION", self.caption)
        base_text = base_text.replace("OPACTIY", str(self.opacity))
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("N_FILTER", str(self.n_filter))
        base_text = base_text.replace("S_FILTER", str(self.s_filter))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("WIDTH", str(self.depth * depth_factor))
        base_text = base_text.replace("DEPTH", str(self.width))

        return base_text


class Spacer(Layer):
    def __init__(self, name: str = None, width: int = 15):
        self.hidden_name = name
        self.width = width
        self.to = None

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic at TO
        {
            Box={
                name=NAME,
                caption= ,
                xlabel={{" ","dummy"}},
                zlabel= ,
                fill=\SoftmaxColor,
                opacity=0.0,
                height=0.0,
                width=WIDTH,
                depth=0.0
            }
        };
        \draw [connection]  (NAME-west) -- node {\midarrow} (NAME-east);
        """

        if not self.name:
            self.hidden_name = f"spacer_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("WIDTH", str(self.width))
        base_text = base_text.replace("TO", self.to)

        return base_text


class ConvConvRelu(Layer):
    def __init__(
        self,
        # shape: list[int],
        s_filter=256,
        n_filter=64,
        name: str = None,
        offset="(0,0,0)",
        to=None,
        opacity=0.9,
        caption=" ",
    ):
        self.hidden_name = name
        self.s_filter = s_filter
        self.n_filter = ",".join([str(val) for val in n_filter])
        self.offset = offset
        self.to = to
        self.width = self.s_filter
        self.height = self.s_filter
        self.depth = [val for val in n_filter]
        self.opacity = opacity
        self.caption = caption

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            RightBandedBox={
                name=NAME,
                caption=CAPTION,
                xlabel={{ N_FILTER }},
                zlabel=S_FILTER,
                fill=\ConvColor,
                bandfill=\ConvReluColor,
                height=HEIGHT,
                width={ WIDTH },
                depth=DEPTH
            }
        };
        """

        if not self.hidden_name:
            self.hidden_name = f"convconv_relu_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("N_FILTER", self.n_filter)
        base_text = base_text.replace("S_FILTER", str(self.s_filter))
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace(
            "WIDTH", ",".join([str(val * depth_factor) for val in self.depth])
        )
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.width))
        base_text = base_text.replace("CAPTION", str(self.caption))

        return base_text


class Pool(Layer):
    def __init__(
        self,
        shape: list[int],
        name: str = None,
        offset: str = "(0,0,0)",
        to=None,
        opacity=0.75,
        caption=" ",
    ):
        self.hidden_name = name
        self.offset = offset
        self.to = to
        self.width = shape[0]
        self.height = shape[1]
        self.depth = shape[2]
        self.caption = caption
        self.opacity = opacity

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Box={
                name=NAME,
                caption=CAPTION,
                fill=\PoolColor,
                opacity=OPACITY,
                height=HEIGHT,
                width=WIDTH,
                depth=DEPTH
            }
        };
        """

        if not self.name:
            self.hidden_name = f"pool_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(self.depth * depth_factor))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.width))
        base_text = base_text.replace("CAPTION", str(self.caption))
        base_text = base_text.replace("OPACITY", str(self.opacity))

        return base_text


class UnPool(Layer):
    def __init__(
        self,
        name,
        offset="(0,0,0)",
        to=None,
        width=1,
        height=32,
        depth=32,
        opacity=0.5,
        caption=" ",
    ):
        self.hidden_name = name
        self.offset = offset
        self.to = to
        self.width = width
        self.height = height
        self.depth = depth
        self.caption = caption

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Box={
                name=NAME,
                caption=CAPTION,
                fill=\UnpoolColor,
                opacity=OPACTIY,
                height=HEIGHT,
                width=WIDTH,
                depth=DEPTH
            }
        };
        """

        if not self.name:
            self.hidden_name = f"unpool_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(depth_factor * self.width))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.depth))
        base_text = base_text.replace("CAPTION", str(self.caption))
        base_text = base_text.replace("OPACITY", str(self.opacity))

        return base_text


class ConvRes(Layer):
    def __init__(
        self,
        name,
        s_filer=256,
        n_filer=64,
        offset="(0,0,0)",
        to=None,
        width=6,
        height=40,
        depth=40,
        opacity=0.2,
        caption=" ",
    ):
        self.hidden_name = name
        self.s_filer = s_filer
        self.n_filer = n_filer
        self.offset = offset
        self.to = to
        self.width = width
        self.height = height
        self.depth = depth
        self.caption = caption
        self.opacity = opacity

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO 
        {
            RightBandedBox={
                name=NAME,
                caption=CAPTION,
                xlabel={{ N_FILER, }},
                zlabel=S_FILER,
                fill={rgb:white,1;black,3},
                bandfill={rgb:white,1;black,2},
                opacity=OPACITY,
                height=HEIGHT,
                width=WIDTH,
                depth=DEPTH
            }
        };
        """

        if not self.name:
            self.hidden_name = f"convres_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("N_FILER", str(self.n_filer))
        base_text = base_text.replace("S_FILER", str(self.s_filer))
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(depth_factor * self.width))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.depth))
        base_text = base_text.replace("CAPTION", str(self.caption))
        base_text = base_text.replace("OPACITY", str(self.opacity))

        return base_text


class ConvSoftmax(Layer):
    def __init__(
        self,
        name,
        s_filer=40,
        offset="(0,0,0)",
        to=None,
        width=1,
        height=40,
        depth=40,
        caption=" ",
    ):
        self.hidden_name = name
        self.s_filer = s_filer
        self.offset = offset
        self.to = to
        self.width = width
        self.height = height
        self.depth = depth
        self.caption = caption

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Box={
                name=NAME,
                caption=CAPTION,
                zlabel=S_FILER,
                fill=\SoftmaxColor,
                height=HEIGHT,
                width=WIDTH,
                depth=DEPTH
            }
        };
        """

        if not self.name:
            self.hidden_name = f"convsoftmax_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("S_FILER", str(self.s_filer))
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(depth_factor * self.width))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.depth))
        base_text = base_text.replace("CAPTION", str(self.caption))

        return base_text


class Softmax(Layer):
    def __init__(
        self,
        shape: int,
        s_filer: int = 10,
        name: str = None,
        offset: str = "(0,0,0)",
        to: str = None,
        opacity: float = 1,
        caption: str = " ",
    ):
        self.hidden_name = name
        self.s_filer = s_filer
        self.offset = offset
        self.to = to
        self.width = 2
        self.height = 2
        self.depth = shape
        self.caption = caption
        self.opacity = opacity

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Box={
                name=NAME,
                caption=CAPTION,
                xlabel={{" ","dummy"}},
                zlabel=S_FILER,
                fill=\SoftmaxColor,
                opacity=OPACITY,
                height=HEIGHT,
                width=WIDTH,
                depth=DEPTH
            }
        };
        """
        if not self.name:
            self.hidden_name = f"softmax_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("S_FILER", str(self.s_filer))
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(self.width))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.depth))
        base_text = base_text.replace("OPACITY", str(self.opacity))
        base_text = base_text.replace("CAPTION", str(self.caption))

        return base_text


class Dense(Layer):
    def __init__(
        self,
        s_filer: int = 10,
        name: str = None,
        offset: str = "(0,0,0)",
        to: str = None,
        opacity: float = 0.9,
        caption: str = " ",
    ):
        self.hidden_name = name
        self.s_filer = s_filer
        self.offset = offset
        self.to = to
        self.width = 2
        self.height = 2
        self.depth = s_filer
        self.caption = caption
        self.opacity = opacity

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Box={
                name=NAME,
                caption=CAPTION,
                xlabel={{" ","dummy"}},
                zlabel=S_FILER,
                fill=\DenseColor,
                opacity=OPACITY,
                height=HEIGHT,
                width=WIDTH,
                depth=DEPTH
            }
        };
        """

        if not self.name:
            self.hidden_name = f"dense_{idx}"

        base_text = base_text.replace("NAME", self.name)
        base_text = base_text.replace("S_FILER", str(self.s_filer))
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("WIDTH", str(self.width))
        base_text = base_text.replace("HEIGHT", str(self.height))
        base_text = base_text.replace("DEPTH", str(self.depth))
        base_text = base_text.replace("OPACITY", str(self.opacity))
        base_text = base_text.replace("CAPTION", str(self.caption))

        return base_text


class Sum(Layer):
    def __init__(
        self,
        name: str,
        offset: str = "(0,0,0)",
        to: str = "(0,0,0)",
        radius: float = 2.5,
        opacity: float = 0.6,
    ):
        self.name = name
        self.offset = offset
        self.to = to
        self.radius = radius
        self.opacity = opacity

    def text(self, depth_factor: float = 1.0, idx: int = None):
        base_text = r"""
        \pic[shift={OFFSET}] at TO
        {
            Ball={
                name=NAME,
                fill=\SumColor,
                opacity=OPACITY,
                radius=RADIUS,
                logo=$+$
            }
        };
        """

        if not self.name:
            self.hidden_name = f"sum_{idx}"

        base_text = base_text.replace("NAME", self.ame)
        base_text = base_text.replace("OFFSET", self.offset)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("RADIUS", str(self.radius))
        base_text = base_text.replace("OPACITY", str(self.opacity))

        return base_text


class Skip(Layer):
    def __init__(self, of: str, to: str, pos: float = 1.25):
        self.name = None
        self.of = of
        self.to = to
        self.pos = pos

    def text(self, depth_factor: float = 1, idx: int = None):
        base_text = r"""
        \path (OF-southeast) -- (OF-northeast) coordinate[pos=POS] (OF-top);
        \path (TO-south)  -- (TO-north) coordinate[pos=POS] (TO-top);
        \draw [copyconnection] (OF-northeast) -- node {\copymidarrow}(OF-top) -- node {\copymidarrow}(TO-top) -- node {\copymidarrow}(TO-north);
        """
        if not self.name:
            self.hidden_name = f"skip_{self.of}_to_{self.to}"

        base_text = base_text.replace("OF", self.of)
        base_text = base_text.replace("TO", self.to)
        base_text = base_text.replace("POS", str(self.pos))

        return base_text


class DottedLines(Layer):
    def __init__(self, of: str, to: str):
        self.hidden_name = None
        self.of = of
        self.to = to

    def text(self, depth_factor: float = 1, idx: int = None):
        base_text = r"""
        \draw[densely dashed]
        (OF-nearnortheast) -- (TO-nearnorthwest)
        (OF-nearsoutheast) -- (TO-nearsouthwest)
        (OF-farsoutheast)  -- (TO-farsouthwest)
        (OF-farnortheast)  -- (TO-farnorthwest)
        ;"""

        if not self.name:
            self.hidden_name = f"dotted_lines_{self.of}_to_{self.to}"

        base_text = base_text.replace("OF", self.of)
        base_text = base_text.replace("TO", self.to)

        return base_text


class End(Layer):
    def __init__(self):
        self.hidden_name = "end"

    def text(self, depth_factor: float = 1.0, idx: int = None):
        return r"""
        \end{tikzpicture}
        \end{document}
        """
