import os
import PyQt5
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
import PyQt5.QtWidgets as Qt# QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
import logging
import sys
import argparse
import importlib
import numpy as np
import inspect
from importlib.metadata import version  

from ergastirio.experiment import experiment
import ergastirio.utils

class MainWindow(Qt.QMainWindow):
    '''
    The main window contains several menus and a QMdiArea object, 
    The QMdiArea object in turn contains subwindows where instruments, plots, data table and logs will be created
    Object creation:
        window = MainWindow()
    The QMdiArea object is saved as attribute:
        window.mdi 
    The mdi object is also the parent object which needs to be passed as parameter when creating an instance of the experiment object
    For example:
        Experiment = experiment(app,window,window.mdi,config_file)
    The mdi object contains a dictionary, window.mdi.containers whose elements represent the different subwindows.
    Specifically, window.mdi.containers = {'logging':{...},'tabledata':{...},'instruments':{...},'plots':{...} }
    The object
        window.mdi.containers[name]['container']
    is the widget that will act as container for the different part of the gui. 
    Each of this widget is a child (via setWidget() method) of a corresponding QScrollArea object, 
        window.mdi.containers[name]['scrollarea']
    In turns, the scrollarea objects are children (via setWidget() method) of corresponding QMdiSubWindow objects
        window.mdi.containers[name]['subwindow']
    '''
    _views =  {'View 1':{
                "instruments":  [ "2/3", "0", "1/3", "2/3" ],
                "plots":        [ "0", "0", "2/3", "2/3" ],
                "tabledata":    [ "0", "2/3", "2/3", "1/3" ],
                "logging":      [ "2/3", "2/3", "1/3", "1/3" ]
                }
               ,
               'View 2':{
                "instruments":  [ "1/2", "0", "1/2", "1/2"],
                "plots":        [ "0", "0", "1/2", "1/2" ],
                "tabledata":    [ "0", "1/2", "1/2", "1/2" ],
                "logging":      [ "1/2", "1/2", "1/2", "1/2" ]
                }
               ,
               'View 3':{
                "instruments":  [ "2/3", "0", "1/3", "1/2"],
                "plots":        [ "0", "0", "2/3", "1/2" ],
                "tabledata":    [ "0", "1/2", "2/3", "1/2" ],
                "logging":      [ "2/3", "1/2", "1/3", "1/2" ]
                }
               ,
               'View 4':{
                "instruments":  [ "2/3", "0", "1/3", "1/2"],
                "plots":        [ "0", "0", "2/3", "3/5" ],
                "tabledata":    [ "0", "3/5", "2/3", "2/5" ],
                "logging":      [ "2/3", "1/2", "1/3", "1/2" ]
                }
               }
    _default_view = 'View 4'
    _mdi_panels ={  'logging':{'title':'Logging'},
                    'tabledata':{'title':'Data acquisition'},
                    'instruments':{'title':'Instruments'},
                    'plots':{'title':'Plots'}
                      }

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__package__} (v{version(__package__)})")
        self.mdi = Qt.QMdiArea()
        mdi_panels = self._mdi_panels
        self.setCentralWidget(self.mdi)

        #This dictionary will be used to create the subwindows of the mdi, and also to populate the "View" menu
  
        self.current_view = self._views[self._default_view]

        bar = self.menuBar()

        file = bar.addMenu("File")
        file.addAction("New Experiment")

        view = bar.addMenu("View")
        for k in self._views.keys():
            view.addAction(k)
        view.triggered[Qt.QAction].connect(self.action_view)
        
        showhide = bar.addMenu("Show/Hide")
        for mdi_panel in mdi_panels.values():
            showhide.addAction(mdi_panel['title'])
        showhide.triggered[Qt.QAction].connect(self.action_showhide)
        
        #Create the different subdiwndows, based on the element of the dictionary mdi_panels
        for key,mdi_panel in mdi_panels.items():
            mdi_panels[key]['subwindow'] = Qt.QMdiSubWindow()
            mdi_panels[key]['subwindow'].setWindowFlags(QtCore.Qt.CustomizeWindowHint)
            mdi_panels[key]['subwindow'].setWindowTitle(mdi_panels[key]['title'])
            mdi_panels[key]['scrollarea'] = Qt.QScrollArea(self)
            #mdi_panels[key]['scrollarea'].verticalScrollBar().rangeChanged.connect(lambda : self.adjust_position_scroll_area(mdi_panels[key]['scrollarea']))
            #mdi_panels[key]['scrollarea'].verticalScrollBar().rangeChanged.connect(lambda: mdi_panels[key]['scrollarea'].verticalScrollBar().setValue(mdi_panels[key]['scrollarea'].verticalScrollBar().maximum()))
            mdi_panels[key]['container'] = Qt.QWidget(self)
            mdi_panels[key]['subwindow'].setWidget(mdi_panels[key]['scrollarea'])
            mdi_panels[key]['scrollarea'].setWidget(mdi_panels[key]['container'])
            mdi_panels[key]['scrollarea'].setWidgetResizable(True)
            self.mdi.addSubWindow(mdi_panels[key]['subwindow'])
            mdi_panel['container'].show()
        self.mdi.containers = mdi_panels

        self.set_view(self._views[self._default_view])

    def action_view(self, p):
        for k in self._views.keys():
            if p.text() == k:
                self.current_view = self._views[k]
                self.set_view(self._views[k])
        return

    def action_showhide(self,p):
        for mdi_panel in self.mdi.containers.values():
            if p.text() == mdi_panel['title']:
                mdi_panel['subwindow'].setHidden(not mdi_panel['subwindow'].isHidden())

    def resizeEvent(self, event):
        Qt.QMainWindow.resizeEvent(self, event)
        if hasattr(self,'current_view'):
            self.set_view(self.current_view)
        
    def closeEvent(self, event=None):
        if self.experiment:
            self.experiment.close_experiment()

    def set_view(self,view):
        geomMDI = self.mdi.geometry()
        MDI_width = geomMDI.width()
        MDI_height = geomMDI.height()
        MDI_x = geomMDI.x()
        MDI_y = geomMDI.y()
        for panel,geom in view.items():
            geom_abs = [] 
            geom_abs.append(    int(ergastirio.utils.convert_fraction_to_float(geom[0])*MDI_width)  )
            geom_abs.append(    int(ergastirio.utils.convert_fraction_to_float(geom[1])*MDI_height) )
            geom_abs.append(    int(ergastirio.utils.convert_fraction_to_float(geom[2])*MDI_width)  )
            geom_abs.append(    int(ergastirio.utils.convert_fraction_to_float(geom[3])*MDI_height) )
            self.mdi.containers[panel]['subwindow'].setGeometry(*geom_abs)

def main():
    parser = argparse.ArgumentParser(description = "",epilog = "")
    parser.add_argument('-e', 
                        help=f"Path of .json file contaning the configuration of this experiment",
                        action="store", dest="config", type=str, default=None)
    parser.add_argument("-s", "--decrease_verbose", help="Decrease verbosity.", action="store_true")
    args = parser.parse_args()
    
    app = Qt.QApplication(sys.argv)
    window = MainWindow()
    
    app.aboutToQuit.connect(window.closeEvent) 

    if args.config:
        config_file = os.path.abspath(args.config)
    else:
        folder_default_file = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(folder_default_file,'config_default.json')

    Experiment = experiment(app,window,window.mdi,config_file)

    window.show()
    app.exec()# Start the event loop.

if __name__ == '__main__':
    main()