from PyQt5 import uic
from PyQt5.QtWidgets import QApplication

import pyqtgraph as pg
pg.setConfigOption('background', (255, 255, 255))  # Do before any widgets drawn
pg.setConfigOption('foreground', 'k')  # Do before any widgets drawn
pg.setConfigOptions(imageAxisOrder='row-major')

Form, Window = uic.loadUiType('pyote.ui')

app = QApplication([])
window = Window()
form = Form()

form.setupUi(window)
print(form.markDzone)
# Change pyqtgraph plots to be black on white

window.show()
app.exec()
