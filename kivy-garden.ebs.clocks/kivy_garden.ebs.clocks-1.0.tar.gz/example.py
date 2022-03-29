

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.ebs.clocks import SimpleDigitalClock


class ClockExampleApp(App):
    def build(self):
        w = BoxLayout(size_hint=(1, 1))
        clock = SimpleDigitalClock(bold=True, font_size='120sp')
        w.add_widget(clock)
        return w


ClockExampleApp().run()
