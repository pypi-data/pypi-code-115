""" A boxplot visualization in Kivy

Running this module will display sample box plots.
"""

from typing import Union, Iterable, Tuple
import numpy as np
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, BooleanProperty
from kivy.lang.builder import Builder
from kwidgets.dataviz.math import BoxPlotData

Builder.load_string("""
<BoxPlot>:
    on_height: self._computeAB()
    canvas:
        # draw a couple invisible lines to make the _axis_range property bound to the redraw
        Color:
            rgba: 0, 0, 0, 0
        Line:
            points: self.width-1, self.y+self._bp+self._op+(self._a*self._axis_range[0]+self._b), self.width+1, self.y+self._bp+self._op+(self._a*self._axis_range[0]+self._b)
        Line:
            points: self.width-1, self.y+self._bp+self._op+(self._a*self._axis_range[1]+self._b), self.width+1, self.y+self._bp+self._op+(self._a*self._axis_range[1]+self._b)
        Color:
            rgba: self._boxcolor
        Line:
            # box around 1st and 3rd quartiles
            rectangle: self.x+self._bp, self.y+self._bp+self._op+(self._a*self._bpd.q1+self._b), self.width - 2*self._bp, self._a*(self._bpd.q3-self._bpd.q1)
        Line:
            # the median
            points: self.x+self._bp, self.y+self._bp+self._op+(self._a*self._bpd.median+self._b), self.x+self.width-self._bp, self.y+self._bp+self._op+(self._a*self._bpd.median+self._b) 
        Line:
            # the vertical line below the box
            points: self.x+self.width/2, self.y+self._bp+self._op+(self._a*self._bpd.q1+self._b), self.x+self.width/2, self.y+self._bp+self._op+(self._a*self._bpd.min+self._b)
        Line:
            # the horizontal line indicating 1st quartile minus 1.5 IQR
            points: self.x+self._bp,  self.y+self._bp+self._op+(self._a*self._bpd.min+self._b), self.x+self.width-self._bp,  self.y+self._bp+self._op+(self._a*self._bpd.min+self._b) 
        Line:
            # the vertical line above the box
            points: self.x+self.width/2, self.y+self._bp+self._op+(self._a*self._bpd.q3+self._b), self.x+self.width/2, self.y+self._bp+self._op+(self._a*self._bpd.max+self._b)
        Line:
            # the horizontal line indicating the 3rd quartile plut 1.5 IQR
            points: self.x+self._bp,  self.y+self._bp+self._op+(self._a*self._bpd.max+self._b), self.x+self.width-self._bp,  self.y+self._bp+self._op+(self._a*self._bpd.max+self._b) 
        Color:
            rgba: self._markercolor
        Ellipse:
            pos: self.x+self.width/2-8,  (self.y+self._bp+2.*self._op+(self._a*self._bpd.max+self._b) if self._markervalue>self._bpd.max else ((self.y+self._bp+(self._a*self._bpd.min+self._b)) if self.markervalue<self._bpd.min else (self.y+self._bp+self._op+(self._a*self._markervalue+self._b))))-8
            size: 16, 16
        Color:
            rgba: self._boxcolor
        Line:
            # plot large outliers as extra line
            points: self.x+self._bp+(0.5*(1.0-self.outlier_proportion_large)*(self.width-2*self._bp)), self.y+self._bp+2.*self._op+(self._a*self._bpd.max+self._b), self.x+self.width-self._bp-(0.5*(1.0-self.outlier_proportion_large)*(self.width-2*self._bp)), self.y+self._bp+2.*self._op+(self._a*self._bpd.max+self._b)
        Line:
            # plot small outliers as extra line
            points: self.x+self._bp+(0.5*(1.0-self.outlier_proportion_small)*(self.width-2*self._bp)), self.y+self._bp+(self._a*self._bpd.min+self._b), self.x+self.width-self._bp-(0.5*(1.0-self.outlier_proportion_small)*(self.width-2*self._bp)), self.y+self._bp+(self._a*self._bpd.min+self._b)
""")


class BoxPlot(Widget):
    """ A Kivy boxplot widget.

    It takes pre-computed BoxPlotData objects or raw iterables over numbers an draws a box plot.  Outliers are drawn
    as variable length lines above or below the plots.  It can also plot another value on top of the box as a circle.

    Key Properties:
    * data: assigned as either an instance of BoxPlotData or a list of numbers from which a BoxPlotData object will be
            computed.
    * boxpadding: number of pixels to leave on any side of the box
    * outlierpadding: number of pixels between the top/bottom of the box and the line for outliers
    * boxcolor: RGBA color for the box itself
    * markercolor: RGBA color for the marker that is drawn over the box
    * markervalue: the extra value to plot as a marker.  Expressed in terms of the original data
    * axis_range: A list of two number that indicate the minimum and maximum range of the overall widget.  If not set,
                  the effective range is set by the data being plotted.  If set, the box is drawn within that range.
                  This is useful when plotting multiple boxplots next to each other and wanting them to share a Y
                  range.
    """
    _bpd = ObjectProperty(BoxPlotData(list(np.arange(0, 1.0, 0.1))))
    _a = NumericProperty(0)
    _b = NumericProperty(1)
    _axis_range = ListProperty([0,1])
    _auto_axis = BooleanProperty(True)

    _boxcolor = ListProperty([0, 1, 0, 1])
    _bp = NumericProperty(15)
    _op = NumericProperty(15)

    _markercolor = ListProperty([1, 0, 0, 0])
    _markervalue = NumericProperty(0)
    _markerwidth = NumericProperty(2)

    def _computeAB(self):
        """ Compute values needed to scale data values to pixels.

        Given the range of the plot and the height of the object in pixels,
        computer the parameters for linear computation (ax+b) to convert a
        data value into a pixel location for plotting.
        """
        self._a = float((self.height-2.*(self._bp+self._op))/(self._axis_range[1]-self._axis_range[0]))
        self._b = float(-self._a*self._axis_range[0])

    @property
    def outlier_proportion_large(self) -> float:
        """ For computing the width of the top outlier line

        :return: min(10, num large outliers)/10
        """
        return min(10, len([x for x in self._bpd.outliers if x>self._bpd.max]))/10.

    @property
    def outlier_proportion_small(self) -> float:
        """ For computing the width of the small outlier line

        :return: min(10, num small outliers)/10
        """
        return min(10, len([x for x in self._bpd.outliers if x<self._bpd.min]))/10.

    @property
    def boxpadding(self) -> int:
        """ The number of pixels to use as a border around the box.

        :return: number of pixels
        """
        return self._bp

    @boxpadding.setter
    def boxpadding(self, value: int):
        """ The number of pixels to use as a border around the box.

        :param value: number of pixels
        """
        self._bp = value

    @property
    def outlierpadding(self) -> int:
        """ Number of pixels between the top of the box plot and the line for outliers.

        :return: number of pixels
        """
        return self._op

    @outlierpadding.setter
    def outlierpadding(self, value: int):
        """ Number of pixels between the top of the box plot and the line for outliers.

        :param value: number of pixels
        """
        self._op = value

    @property
    def boxcolor(self) -> Tuple[float, float, float, float]:
        """ The color of the box

        :return: tuple in the form of red, green, blue, alpha
        """
        return self._boxcolor

    @boxcolor.setter
    def boxcolor(self, value: Tuple[float, float, float, float]):
        """ The color of the box

        :param value: tuple in the form of red, green, blue, alpha
        """
        self._boxcolor = value

    @property
    def markercolor(self) -> Tuple[float, float, float, float]:
        """ The color of the marker for the extra plotted value.

        :return: tuple in the form of red, green, blue, alpha
        """
        return self._markercolor

    @markercolor.setter
    def markercolor(self, value: Tuple[float, float, float, float]):
        """ The color of the marker for the extra plotted value

        :param value: tuple in the form of red, green, blue, alpha
        """
        self._markercolor = value

    @property
    def markervalue(self) -> float:
        """ The extra value to plot

        :return: value in the range of the data
        """
        return self._markervalue

    @markervalue.setter
    def markervalue(self, value: float):
        """ The extra value to plot

        :param value: value in the range of the data
        """
        self._markervalue = value

    @property
    def data(self) -> BoxPlotData:
        """ The math.BoxPlotData object being plotted.

        :return:
        """
        return self._bpd

    @data.setter
    def data(self, data: Union[BoxPlotData, Iterable[Union[float, int]]]):
        """ Sets the data being plotted.

        :param data: If an instances of BoxPlotData, just use that object.  Otherwise, create a new BoxPlotData object
        from the list of numbers provided.
        """
        if isinstance(data, BoxPlotData):
            bpd = data
        else:
            bpd = BoxPlotData(data)
        self._bpd = bpd
        if self._auto_axis:
            self._axis_range = (bpd.min, bpd.max)
        self._computeAB()

    @property
    def axis_range(self) -> Tuple[float, float]:
        """ The range of the plot.

        In the even that multiple boxplot are displayed next to each other (or for some other reason), it might be
        useful to manually specify the range of the databeing ploted.  If no axis range is manually specified, this
        will simply be the BoxPlotData's min,max values.  If manually specified, it will be the manually specified values.

        :return: a tuple in the form of (min, max)
        """
        return self._axis_range

    @axis_range.setter
    def axis_range(self, minmax: Tuple[float, float]):
        """ Manually set the range for the box plot.

        This method will both set the range and prevent the range from changing if the boxplot data is set later.

        :param minmax: tuple in the form of  (min, max)
        """
        self._axis_range = minmax
        self._auto_axis = False
        self._computeAB()


class BoxPlotApp(App):
    def build(self):
        container = Builder.load_string('''
#:import np numpy
BoxLayout:
    orientation: 'horizontal'
    BoxLayout
        orientation: 'vertical'
        Label:
            size_hint: 1, .1
            text: "Random Normal"
        BoxPlot:
            boxcolor: 1,0,0,1
            data: np.random.normal(0, 2, 500)
    BoxLayout
        orientation: 'vertical'
        Label:
            size_hint: 1, .1
            text: "Random Uniform"
        BoxPlot:
            data: np.random.uniform(0, 10, 500)
            markercolor: .7, .7, 1, 1
            markervalue: 1.5
    BoxLayout
        orientation: 'vertical'
        Label:
            size_hint: 1, .1
            text: "Random Gamma"
        BoxPlot:
            data: np.random.gamma(2, 2, 500)
            markervalue: 15
            markercolor: 1, 0, 0, 1
    BoxLayout
        orientation: 'vertical'
        Label:
            size_hint: 1, .1
            halign: 'center'
            text: "Random Normal\\n(fixed range)"
        BoxPlot:
            boxcolor: 1,0,0,1
            data: np.random.normal(3, 2.5, 500)
            axis_range: -10, 10
            markervalue: -100
            markercolor: 0, 1, 0, 1
    BoxLayout
        orientation: 'vertical'
        Label:
            size_hint: 1, .1
            halign: 'center'
            text: "Random Normal\\n(fixed range)"
        BoxPlot:
            boxcolor: 1,0,0,1
            data: np.random.normal(-1, 3, 500)
            axis_range: -10, 10
        
''')
        return container


if __name__ == "__main__":
    BoxPlotApp().run()
