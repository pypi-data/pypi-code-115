import os
import PyQt5.QtWidgets as Qt# QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
import logging
import ergastirio.utils

graphics_dir = os.path.join(os.path.dirname(__file__), 'graphics')

'''
The panels defined in this module are meant to be ONLY gui for other classes, i.e. their event are directly connected to methods of other objects
do not have their own logger, and they do not produce any logging event. Rather, they are "directly" connected to methods and functionalities
of the experiment object
'''

class acquisition_control():

    def __init__(self, app, mainwindow, parent, experiment):
        # app           = The pyqt5 QApplication() object
        # mainwindow    = Main Window of the application
        # parent        = a QWidget (or QMainWindow) object that will be the parent of this gui
        # experiment    = an experiment() object, whose acquisition will be controlled by this panel

        self.mainwindow = mainwindow
        self.app = app
        self.parent = parent
        self.experiment  = experiment 

    def create_gui(self): 

        hbox = Qt.QHBoxLayout()
        vbox_acquisition = Qt.QVBoxLayout()

        box_acquisition = Qt.QGroupBox() 
        box_acquisition.setTitle(f"Acquisition modality")
        vbox = Qt.QVBoxLayout()
        vbox_acquisition_row1 = Qt.QHBoxLayout()
        vbox_acquisition_row2 = Qt.QHBoxLayout()
        vbox_acquisition_row3 = Qt.QHBoxLayout()

        vbox_trigger = Qt.QVBoxLayout()
        box_trigger = Qt.QGroupBox() 
        box_trigger.setTitle(f"Trigger")
        box_trigger_vbox = Qt.QVBoxLayout()

        self.button_StartPauseContinuousAcquisition = Qt.QPushButton()
        self.button_StartPauseContinuousAcquisition.setToolTip('Start or pause triggered data acquisition. Each time a trigger (either internal or by instruments) is received, \nit takes a single set of acquisitions, with the number of acquisitions and time interval specified here below.') 
        self.button_StartPauseContinuousAcquisition.clicked.connect(self.click_button_StartPauseContinuousAcquisition)

        self.button_SingleAcquisition = Qt.QPushButton("Take single set acquisitions")
        self.button_SingleAcquisition.setToolTip('Triggers a single set of acquisitions, with the number of acquisitions and time interval specified here below.') 
        self.button_SingleAcquisition.clicked.connect(self.click_button_SingleAcquisition)
            
        self.label_NumbAcquisitions = Qt.QLabel("Number of acquisitions per set = ")
        self.spinbox_NumbAcquisitions = Qt.QSpinBox()
        self.spinbox_NumbAcquisitions.setRange(1, 100)
        self.spinbox_NumbAcquisitions.valueChanged.connect(self.value_changed_spinbox_NumbAcquisitions)
        self.box_MakeAverage = Qt.QCheckBox("and average")
        self.box_MakeAverage.stateChanged.connect(self.click_box_MakeAverage)
        self.box_MakeAverage.setToolTip('When checked, the multiple acquisitions are averaged.')

        self.label_AcquisitionRefreshTime= Qt.QLabel("Separated by (s) = ")
        self.edit_AcquisitionRefreshTime = Qt.QLineEdit()
        self.edit_AcquisitionRefreshTime.setText(str(self.experiment.refresh_time_multiple_acquisitions))
        self.edit_AcquisitionRefreshTime.returnPressed.connect(self.press_enter_edit_AcquisitionRefreshTime)
        self.edit_AcquisitionRefreshTime.setAlignment(QtCore.Qt.AlignRight)
        self.edit_AcquisitionRefreshTime.setStyleSheet("background-color: #FFFFFF;")

        vbox_acquisition_row1.addWidget(self.button_StartPauseContinuousAcquisition)
        vbox_acquisition_row1.addWidget(self.button_SingleAcquisition)
        vbox_acquisition_row2.addWidget(self.label_NumbAcquisitions)
        vbox_acquisition_row2.addWidget(self.spinbox_NumbAcquisitions)
        vbox_acquisition_row2.addWidget(self.box_MakeAverage)
        vbox_acquisition_row3.addWidget(self.label_AcquisitionRefreshTime)
        vbox_acquisition_row3.addWidget(self.edit_AcquisitionRefreshTime)
        vbox.addLayout(vbox_acquisition_row1)
        vbox.addLayout(vbox_acquisition_row2)
        vbox.addLayout(vbox_acquisition_row3)
        box_acquisition.setLayout(vbox)
        vbox_acquisition.addWidget(box_acquisition)
        
        self.panelGlobal = Qt.QWidget()
        self.panelGlobal.setStyleSheet("background-color: #D3D3D3;")
        layout = Qt.QHBoxLayout(self.panelGlobal)
        self.radio_TriggerGlobal = Qt.QRadioButton()
        self.radio_TriggerGlobal.setText("Internal")
        self.radio_TriggerGlobal.setStyleSheet("QRadioButton { font: bold;}");
        self.radio_TriggerGlobal.setChecked(True)
        self.radio_TriggerGlobal.value= "global"
        self.radio_TriggerGlobal.clicked.connect(self.click_radio_global_instrument)
        self.radio_TriggerGlobal.setToolTip('In this modality, data from all instruments is acquired at periodic inteverals of time, set by the \'refresh time\'. \nNote: user must check that each instrument is running and refreshing its own data.') 
        self.label_RefreshTime = Qt.QLabel("refresh time (s) = ")
        self.edit_RefreshTime = Qt.QLineEdit()
        self.edit_RefreshTime.setText(str(self.experiment.refresh_time_internal_trigger))
        self.edit_RefreshTime.returnPressed.connect(self.press_enter_edit_RefreshTime)
        self.edit_RefreshTime.setAlignment(QtCore.Qt.AlignRight)
        self.edit_RefreshTime.setStyleSheet("background-color: #FFFFFF;")
        layout.addWidget(self.radio_TriggerGlobal)
        layout.addWidget(self.label_RefreshTime)
        layout.addWidget(self.edit_RefreshTime)
        layout.addStretch(1)

        self.panelTrigger = Qt.QWidget()
        self.panelTrigger.setStyleSheet("background-color: #D3D3D3;")
        layout = Qt.QHBoxLayout(self.panelTrigger)
        self.radio_TriggerInstrument = Qt.QRadioButton()
        self.radio_TriggerInstrument.setText("By Instrument")
        self.radio_TriggerInstrument.setStyleSheet("QRadioButton { font: bold;}");
        self.radio_TriggerInstrument.value= "by_instrument"
        self.radio_TriggerInstrument.clicked.connect(self.click_radio_global_instrument)
        self.radio_TriggerInstrument.setToolTip('In this modality, one instrument is designated as trigger. Whenever that instrument updates its own data, it triggers an acquisition.') 
        self.label_TriggerInstrument = Qt.QLabel(" = ")
        self.combo_TriggerInstruments = Qt.QComboBox()
        self.combo_TriggerInstruments.resize(self.combo_TriggerInstruments.sizeHint())
        self.combo_TriggerInstruments.currentIndexChanged.connect(self.change_combo_TriggerInstruments)
        self.combo_TriggerInstruments.setStyleSheet("background-color: #FFFFFF;")
        self.label_TriggerInstrumentDelay = Qt.QLabel(", delayed  by (s) = ")
        self.edit_TriggerInstrumentDelay = Qt.QLineEdit()
        self.edit_TriggerInstrumentDelay.setText(str(self.experiment.trigger_delay))
        self.edit_TriggerInstrumentDelay.setStyleSheet("background-color: #FFFFFF;")
        self.edit_TriggerInstrumentDelay.returnPressed.connect(self.press_enter_edit_TriggerInstrumentDelay)
        self.edit_TriggerInstrumentDelay.setAlignment(QtCore.Qt.AlignRight)
        layout.addWidget(self.radio_TriggerInstrument)
        layout.addWidget(self.label_TriggerInstrument)
        layout.addWidget(self.combo_TriggerInstruments)
        layout.addWidget(self.label_TriggerInstrumentDelay)
        layout.addWidget(self.edit_TriggerInstrumentDelay)
        layout.addStretch(1)
        
        self.buttongroup_trigger = Qt.QButtonGroup(self.parent)
        self.buttongroup_trigger.addButton(self.radio_TriggerGlobal)
        self.buttongroup_trigger.addButton(self.radio_TriggerInstrument)

        box_trigger_vbox.addWidget(self.panelGlobal)
        box_trigger_vbox.addWidget(self.panelTrigger)
        box_trigger.setLayout(box_trigger_vbox)
        vbox_trigger.addWidget(box_trigger)
        
        hbox.addLayout(vbox_acquisition)  
        hbox.addStretch(1)
        hbox.addLayout(vbox_trigger) 
        
        self.parent.setLayout(hbox) #This line makes sure that all widgest defined so far are assigned to the widget defines in self.parent
        self.parent.resize(self.parent.minimumSize())
        #The widgets in this list will be enabled when we are NOT continuosly acquiring
        self.widgets_enabled_when_not_continous_acquisition = [ self.button_StartPauseContinuousAcquisition,
                                                                self.button_SingleAcquisition,
                                                                self.spinbox_NumbAcquisitions,
                                                                self.box_MakeAverage,
                                                                self.label_NumbAcquisitions,
                                                                self.label_AcquisitionRefreshTime,
                                                                self.edit_AcquisitionRefreshTime,
                                                                self.radio_TriggerGlobal,
                                                                self.label_RefreshTime,
                                                                self.edit_RefreshTime,
                                                                self.label_TriggerInstrument,
                                                                self.label_TriggerInstrumentDelay,
                                                                self.radio_TriggerInstrument,
                                                                self.combo_TriggerInstruments,
                                                                self.edit_TriggerInstrumentDelay]

        #The widgets in this list will be enabled when we are continuosly acquiring
        self.widgets_enabled_when_continous_acquisition = [ self.button_StartPauseContinuousAcquisition ]
        #The widgets in this list will be disabled when we are continuosly acquiring
        self.widgets_disabled_when_continous_acquisition = [self.button_SingleAcquisition,
                                                            self.spinbox_NumbAcquisitions,
                                                            self.box_MakeAverage,
                                                            self.label_NumbAcquisitions,
                                                            self.label_AcquisitionRefreshTime,
                                                            self.edit_AcquisitionRefreshTime,
                                                            self.radio_TriggerGlobal,
                                                            self.label_RefreshTime,
                                                            self.edit_RefreshTime,
                                                            self.label_TriggerInstrument,
                                                            self.label_TriggerInstrumentDelay,
                                                            self.radio_TriggerInstrument,
                                                            self.combo_TriggerInstruments,
                                                            self.edit_TriggerInstrumentDelay
                                                            ]
        self.populate_combo_TriggerInstruments()

        #Initialize part of the GUI by mimicking events
        self.click_radio_global_instrument()
        self.set_pause_continous_acquisition_state()
        self.box_MakeAverage.setChecked(self.experiment.average_acquisition)
        #self.click_box_MakeAverage(state= QtCore.Qt.Checked if self.experiment.average_acquisition==True else False)
        return self

    ### GUI Events Functions
    def click_button_StartPauseContinuousAcquisition(self): 
        if(self.experiment.continous_acquisition == False):
            self.press_enter_edit_RefreshTime()
            self.press_enter_edit_AcquisitionRefreshTime()
            self.press_enter_edit_TriggerInstrumentDelay()
            self.start_continous_acquisition()
        elif (self.experiment.continous_acquisition == True):
            self.pause_continous_acquisition()
        return

    def press_enter_edit_RefreshTime(self):
        refresh_time_internal_trigger = self.edit_RefreshTime.text()
        self.experiment.refresh_time_internal_trigger = refresh_time_internal_trigger #When doing this assignment, the self.experiment.refresh_time_internal_trigger setter will take care of checking if refresh_time is valid, and eventually update the value
        self.edit_RefreshTime.setText(f"{self.experiment.refresh_time_internal_trigger:.3f}") #In case refresh_time_internal_trigger is not valid, this instruction will restore the displayed value to its previous (valid) value
        return True
 
    def press_enter_edit_AcquisitionRefreshTime(self):
        acquisition_refresh_time = self.edit_AcquisitionRefreshTime.text()
        self.experiment.refresh_time_multiple_acquisitions = acquisition_refresh_time #When doing this assignment, the self.experiment.refresh_time setter will take care of checking if refresh_time is valid, and eventually update the value
        self.edit_AcquisitionRefreshTime.setText(f"{self.experiment.refresh_time_multiple_acquisitions:.3f}") #In case refresh_time is not valid, this instruction will restore the displayed value to its previous (valid) value
        return True

    def click_button_SingleAcquisition(self):
        self.press_enter_edit_AcquisitionRefreshTime()
        self.experiment.trigger_single_set_acquisition()

    def value_changed_spinbox_NumbAcquisitions(self):
        self.experiment.numb_acquisitions_per_trigger = self.spinbox_NumbAcquisitions.value()

    def click_radio_global_instrument(self):
        if self.radio_TriggerGlobal.isChecked():
            self.experiment.set_trigger_modality('internal')
            self.press_enter_edit_RefreshTime()
            ergastirio.utils.enable_widget([self.edit_RefreshTime,self.label_RefreshTime])
            ergastirio.utils.disable_widget([self.combo_TriggerInstruments,self.edit_TriggerInstrumentDelay,self.label_TriggerInstrument,self.label_TriggerInstrumentDelay])
        if self.radio_TriggerInstrument.isChecked():
            self.experiment.set_trigger_modality('external')
            self.change_combo_TriggerInstruments()
            ergastirio.utils.disable_widget([self.edit_RefreshTime,self.label_RefreshTime])
            ergastirio.utils.enable_widget([self.combo_TriggerInstruments,self.edit_TriggerInstrumentDelay,self.label_TriggerInstrument,self.label_TriggerInstrumentDelay])

    def change_combo_TriggerInstruments(self):
        self.press_enter_edit_TriggerInstrumentDelay()

    def press_enter_edit_TriggerInstrumentDelay(self):
        trigger_delay = self.edit_TriggerInstrumentDelay.text()
        if self.radio_TriggerInstrument.isChecked():
            check = self.experiment.set_trigger_instrument(self.combo_TriggerInstruments.currentText(),delay=trigger_delay)
            if check:
                self.edit_TriggerInstrumentDelay.setText(str(self.experiment.trigger_delay))

    def click_box_MakeAverage(self, state):
        if state == QtCore.Qt.Checked:
            status_bool = True
        else:
            status_bool = False
        print(status_bool)
        self.experiment.set_average_modality(status_bool)

    ### END GUI Events Functions

    def populate_combo_TriggerInstruments(self):
        list_instruments = [instrument['fullname'] for instrument in self.experiment.instruments]
        self.combo_TriggerInstruments.clear()
        self.combo_TriggerInstruments.addItems(list_instruments)  

    def start_continous_acquisition(self):

        self.press_enter_edit_RefreshTime() #We emulate this event to make sure to update the refresh time value
        self.experiment.start_continous_acquisition()
        self.set_continous_acquisition_state() # Change some widgets
        return

    def pause_continous_acquisition(self):
        self.experiment.stop_continous_acquisition()
        self.set_pause_continous_acquisition_state() # Change some widgets
        return

    def set_pause_continous_acquisition_state(self):
        #Changes the GUI based on the state
        self.button_StartPauseContinuousAcquisition.setText('Start triggered acquisition')
        ergastirio.utils.enable_widget(self.widgets_enabled_when_not_continous_acquisition)
        self.click_radio_global_instrument() #mimick a click on radio button to reset the enabled/disabled state of the corresponding widgets

    def set_continous_acquisition_state(self):
        #Changes the GUI based on the state
        self.button_StartPauseContinuousAcquisition.setText('Pause')
        ergastirio.utils.enable_widget(self.widgets_enabled_when_continous_acquisition)
        ergastirio.utils.disable_widget(self.widgets_disabled_when_continous_acquisition)

class data_management():
    def __init__(self, app, mainwindow, parent, experiment):
        # app           = The pyqt5 QApplication() object
        # mainwindow    = Main Window of the application
        # parent        = a QWidget (or QMainWindow) object that will be the parent of this gui
        # experiment    = an experiment() object, whose acquisition will be controlled by this panel
        self.mainwindow = mainwindow
        self.app = app
        self.parent = parent
        self.experiment  = experiment 

    def create_gui(self): 
        hbox1 = Qt.QHBoxLayout()

        self.button_SaveData = Qt.QPushButton("Save data")
        self.button_SaveData.setToolTip('Save all currently stored data in a .csv file.') 
        self.button_SaveData.clicked.connect(self.click_button_SaveData)
        self.button_DeleteAllData = Qt.QPushButton("Delete all data")
        self.button_DeleteAllData.setToolTip('Delete all currently stored data.') 
        self.button_DeleteAllData.clicked.connect(self.click_button_DeleteAllData)
        self.button_DeleteLastRowData = Qt.QPushButton("Delete last row")
        self.button_DeleteLastRowData.setToolTip('Delete last row of stored data.') 
        self.button_DeleteLastRowData.clicked.connect(self.click_button_DeleteLastRowData)

        hbox1.addWidget(self.button_SaveData)
        hbox1.addWidget(self.button_DeleteAllData)
        hbox1.addWidget(self.button_DeleteLastRowData)
        hbox1.addStretch(1)

        vbox = Qt.QVBoxLayout()
        vbox.addLayout(hbox1)  
        vbox.addStretch(1)

        self.parent.setLayout(vbox) #This line makes sure that all widgest defined so far are assigned to the widget defines in self.parent
        self.parent.resize(self.parent.minimumSize())

        return self

    ### GUI Events Functions

    def click_button_SaveData(self): 
        filename, _ = Qt.QFileDialog.getSaveFileName(self.mainwindow, 
                        "Save File", "", "Csv Files (*.csv);;Text Files (*.txt)")
        if filename:
            self.experiment.save_stored_data(filename)
        return

    def click_button_DeleteAllData(self):
        answer = Qt.QMessageBox.question(self.parent,'', "Are you sure?", Qt.QMessageBox.Yes | Qt.QMessageBox.No, Qt.QMessageBox.No)
        if answer == Qt.QMessageBox.Yes:
            self.experiment.delete_current_data()
        return

    def click_button_DeleteLastRowData(self):
        self.experiment.delete_row_from_data(-1)
        return