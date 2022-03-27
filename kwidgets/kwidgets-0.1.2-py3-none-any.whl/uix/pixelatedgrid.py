""" A general purpose display grid

This widget is composed of a rows and column of squares that can be referenced by x and y values.
"""
from numpy import random
from kivy.uix.widget import Widget
from kivy.lang.builder import Builder
from kivy.properties import ListProperty, NumericProperty, ObjectProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line


class PixelatedGrid(Widget):
    """ A general purpose display grid

    This widget is split into rows and columns that are accessible via x and y values.  Each cell is either "activated"
    or "inactivated."  An inactivated cells is some default color and the activated cells take on some other single
    color.  A single pixel grid delineates each cell.  A property "activated_cells" indicates which cells are
    activated.  Every cell is a square with some specified side length.  The number of rows and columns available
    depend on the size of the window, which can change during runtime based of the size of the widget.

    Key properties:
    * background_color - RGBA list for the inactive cell color
    * grid_color - RGBA for the grid lines
    * activated_color - RGBA for the active cell color
    * cell_length - the length of the side of a cell (essentially cell size)
    * activated_cells - a list of tuples indicating the active cells.  For example, to indicate two active cells,
      use ((x1,y1), (x2,y2))
    """
    background_color = ListProperty([0, 0, 0, 1])
    grid_color = ListProperty([47/255, 79/255, 79/255, 1])
    activated_color = ListProperty([0, 1, 0, 1])
    cell_length = NumericProperty(10)
    activated_cells = ObjectProperty(set())

    def __init__(self, **kwargs):
        """ Create a new instance of PixelatedGrid.

        Binds pos, size, and activated_cells to update_canvas.

        :param kwargs:
        """
        super(PixelatedGrid, self).__init__(**kwargs)
        self.bind(pos=self.update_canvas)
        self.bind(size=self.update_canvas)
        self.bind(activated_cells=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        """ Clears and redraws the canvas.

        For efficiency, unactivated cells are drawn as a single large rectangle.  Lines are then drawn to create the
        grid.  Finally, the activated cells are drawn one-by-one.  This is more efficient as long as the number
        of activated cells is less than the number of inactive ones.

        :param args:
        :return:
        """
        self.canvas.clear()
        with self.canvas:
            Color(*self.background_color)
            Rectangle(pos = [self.x,self.y], size=[self.width, self.height])
            Color(*self.grid_color)
            for x in range(0, int(self.width), self.cell_length):
                Line(points=[self.x + x, self.y, self.x + x, self.y + int(self.height)], width=1)
            for y in range(int(self.height), 0, -self.cell_length):
                Line(points=[self.x, self.y + y, self.x + int(self.width), self.y + y], width=1)
            Color(*self.activated_color)
            for x, y in self.activated_cells:
                Rectangle(pos=[self.x+x*self.cell_length, self.y+self.height-(y+1)*self.cell_length], size=[self.cell_length, self.cell_length])

    def visible_width(self) -> int:
        """  The number of visible horizontal cells

        Note that this can change during program execution when the widget is resized.

        :return: The number of horizontal cells.
        """
        return self.width//self.cell_length

    def visible_height(self) -> int:
        """ The number of visible vertical cells

        Note that this can change during program execution when the widget is resized.

        :return: The number of vertical cells
        """
        return self.height//self.cell_length


class PixelatedGridApp(App):

    def activate_random(self, *args):
        num_cells=100
        visible_width = self.container.visible_width()
        visible_height = self.container.visible_height()
        self.container.activated_cells = set([(random.randint(0, visible_width), random.randint(0, visible_height)) for _ in range(0,num_cells)])

    def build(self):
        self.container = Builder.load_string('''
PixelatedGrid:
    id: thegrid
    background_color: 1, 0, 0, .4
    grid_color: 1, 0, 0, .7
''')
        Clock.schedule_interval(self.activate_random, .5)
        return self.container


if __name__ == "__main__":
    PixelatedGridApp().run()
