

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.ebs.marquee import MarqueeLabel


class MarqueeExampleApp(App):
    def build(self):
        w = BoxLayout(size=(500, 200))
        marquee = MarqueeLabel(bgcolor=(0, 0, 0, 0), text="Hello World")
        marquee.start(loop=True)
        w.add_widget(marquee)
        return w


MarqueeExampleApp().run()
