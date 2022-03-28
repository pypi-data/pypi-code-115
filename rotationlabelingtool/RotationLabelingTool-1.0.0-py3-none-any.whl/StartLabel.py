import sys

from PyQt5 import QtWidgets

from RotationLabelingTool.labelingTool import LabelingTool

def StartLabel():
    app = QtWidgets.QApplication(sys.argv)
    application = LabelingTool.LabelingTool()
    application.show()
    sys.exit(app.exec())
