""" A widget for displaying a rotating set of quotations.

Includes an application such that if this module is run directly with a path to a text file containing one quotation
per line, it will rotate through those quotations.
"""
from typing import List, Union
import sys
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.window import Window
import random

Builder.load_string("""
<QuotationDisplay>:
    padding: 50
    canvas:
        Color: 
            rgb: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color: 
            rgba: 1, 1, 1, 1
        Line:
            width: 2.0
            rounded_rectangle: 10, 10, self.width-20, self.height-20, 10, 10, 10, 10
    Label:
        text: root.text
        text_size: self.width-20, self.height-20    
        valign: 'middle'
        halign: 'center'
        font_size: '20sp'
""")


class QuotationDisplay(BoxLayout):
    """ Widget that displays a rotating set of quotations.

    Key Properties:
    * update_sec: The number of seconds before changing the quotation
    * quotations: assigned as either a list of strings, one per quotation, or a single string that is a path to
                  a file with quotations, one per line.
    """
    text = StringProperty(defaultvalue="huh?")
    _update_sec: int = 10
    _quotations: List[str] = ["No quotations specified"]

    def __init__(self, **kwargs):
        """ Create a new QuotationDisplay widget

        :param kwargs:
        """
        super(QuotationDisplay, self).__init__(**kwargs)
        self.event = Clock.schedule_interval(self.update, self.update_sec)

    def update(self, dt):
        """ Display a randomly chosen quotation
        :param dt:
        """
        self.text = random.choice(self._quotations)

    @property
    def update_sec(self) -> int:
        """ Number of seconds between quotation transitions.

        :return:
        """
        return self._update_sec

    @update_sec.setter
    def update_sec(self, value: int):
        """ Set the number of seconds between quotation transitions.  Resets and restarts the schedule for this object.

        :param value: The number of seconds between quotation transitions
        """
        self._update_sec = value
        self.event.cancel()
        self.event = Clock.schedule_interval(self.update, self.update_sec)

    @property
    def quotations(self) -> List[str]:
        """ A list of strings, each of which represents a quotation.

        :return: A list of quotations
        """
        return self._quotations

    @quotations.setter
    def quotations(self, quotations: Union[str, List[str]]):
        """ Set the quotations used by this object.

        :param quotations: Either a list of strings, each of which represent a quotation or a path to a file
        containing one quotation per line.  Also sets a new quotation on the display.
        """
        if isinstance(quotations, str):
            with open(quotations, 'r', encoding="latin-1") as f:
                self._quotations = [l.strip() for l in f.readlines()]
        else:
            self._quotations = quotations
        self.text = random.choice(self._quotations)

_sample_quotations = [
    "If you seek Truth, you will not seek to gain a victory by every possible means; and when you have found Truth, you need not fear being defeated. -Epictetus",
    "If anyone tells you that a certain person speaks ill of you, do not make excuses about what is said of you but answer, 'He was ignorant of my other faults, else he would not have mentioned these alone.' -Epictetus",
    "Every moment think steadily as a Roman and a man to do what thou hast in hand with perfect and simple dignity, and feeling of affection, and freedom, and justice; and to give thyself relief from all other thoughts. -Marcus Aurelius",
    "For nowhere, either with more quiet or more freedom from trouble, does a man retire than into his own soul. -Marcus Aurelius",
    "My conduct might be blameable, but I leave it, without attempting further to excuse it; my present purpose being to relate facts, and not to make apologies for them. -Ben Franklin"
]
class QuotationDisplayApp(App):
    """ Displays a Quotation display with an exit button on the right.

    If a path is provided on the command line, it loads and displays those quotations.
    If "fullscreen" is added
    """
    def build(self):
        container = Builder.load_string('''
#:import exit sys.exit
BoxLayout:
    q: quotation_widget
    QuotationDisplay:
        id: quotation_widget
        size_hint: .9, 1
        update_sec: 10
    BoxLayout:
        size_hint: .1, 1
        Button:
            text: 'X'
            on_press: exit()
''')

        if len(sys.argv) > 2 and ('fullscreen' in sys.argv):
            Window.fullscreen=True
        if len(sys.argv) > 1:
            container.q.quotations = sys.argv[1]
        else:
            container.q.quotations = _sample_quotations
        return container


if __name__ == "__main__":
    QuotationDisplayApp().run()
