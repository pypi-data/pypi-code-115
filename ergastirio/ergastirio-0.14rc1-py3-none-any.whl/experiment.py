import ergastirio.experiment_initializer
import PyQt5.QtCore as QtCore
import logging
import json
import numpy as np
import datetime
import ergastirio.utils

class experiment():
    _config_file = ''
    _verbose = True #Keep track of whether this instance of the interface should produce logs or not
    _name_logger = ''
    data_headers =[]    #List of strings, will contain the label of each 'column" of acquired data, based on the instruments connected, in the format "dev#i_dataname#j"
                        # where #i runs from 0 to the number of instruments minus 1, and dataname#j is the name of the jth data created by the i-th instrument.
                        # the data created by each instrument are specified by the keys of the output dictionary defined in the interface of each instrument
    
    def __init__(self, app, mainwindow, parent, config_file, name_logger=__package__):
        # app           = The pyqt5 QApplication() object
        # mainwindow    = Main Window of the application
        # parent        = a QWidget (or QMainWindow) object that will be the parent for the gui of this device. Normally, this is an mdi object contained in the mainwindow object
        #                 This QWdiget must have an attribute called 'containers' which is a dictionary, containing the following keys
        #                 'logging','tabledata','instruments','plots'
        #                 Each item of parent.containers is a dictionary, and it identifies a different panel  
        #                 For each item, the sub-item with key 'container' is a widget that will host the relative content.
        #                   E.g. parent.containers['plots']['container'] is a QWidget that will host the plots
        # config_file   = a valid .json file containing all settings of this experiment
        # name_logger   = The name of the logger used for this particular experiment. If none is specified, the name of the package (i.e. ergastirio) is used as logger name

        self.mainwindow = mainwindow
        self.app = app
        self.parent = parent
        self.name_logger = name_logger #Setting this property will also create the logger,set defaulat output style, and store the logger object in self.logger (see @name_logger.setter)
        
        ergastirio.experiment_initializer.create_gui_logging(self,self.parent.containers['logging']['container']) #By calling this function here (instead than later inside set_up_experiment_gui() ) we make sure that any log message is shown in the GUI
                                                                                                                    #Need to implement this more elegantly
        self._refresh_time_internal_trigger = 0.1                #in s. Refresh time of internal trigger (when used)
        
        self.continous_acquisition = False      #Boolean variable, true when performing continuous acquisition (i.e. when internal trigger is used)
        self.triggered_acquisition = False      #Boolean variable, true when external trigger is used
        self._numb_acquisitions_per_trigger = 1 #Every time that a trigger is "fired" (either by internal trigger, or by external trigger, 
                                                #or by clicking on 'take single acqusitions') the software takes a number of acquisitions 
                                                #equal to self._numb_acquisitions_per_trigger, and separated in time by self._refresh_time_multiple_acquisitions
        self._refresh_time_multiple_acquisitions = 0.05 #in s 
        self.average_acquisition = True         #When this is set to true, after taking a number of acquisitions (give by self._numb_acquisitions_per_trigger )
                                                #it averages them and replace them by the average
        self.trigger_instrument = ''
        self.trigger_delay = 0

        self.config_file = config_file #Setting the config file name will also automatically open the file and load the settings (see @config_file.setter)
                                                                    
        self.mainwindow.experiment = self

        return

    @property
    def verbose(self):
        return self.verbose
    @verbose.setter
    def verbose(self,verbose):
        #When the verbose property of this interface is changed, we also update accordingly the level of the logger object
        if verbose: loglevel = logging.INFO
        else: loglevel = logging.CRITICAL
        self.logger.setLevel(level=loglevel)

    @property
    def name_logger(self):
        return self._name_logger
    @name_logger.setter
    def name_logger(self,name):
        #Create logger, and set default output style.
        self._name_logger = name
        self.logger = logging.getLogger(self._name_logger)
        self.verbose = self._verbose #This will automatically set the logger verbosity too
        if not self.logger.handlers:
            formatter = logging.Formatter(f"[{self.name_logger}]: %(message)s")
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        self.logger.propagate = False

    @property
    def config_file(self):
        return self._config_file
    @config_file.setter
    def config_file(self,config_file):
        self.logger.info(f"Setting the config file to {config_file}... [Note: this will reset the experiment]")
        self._config_file = config_file
        self.load_config()
        return 

    def load_config(self):
        '''
        Import experiment settings from the .json file stored in self.config_file, and then starts setting up the experiment 
        by calling the function ergastirio.experiment_initializer.setup(self).
        '''
        self.logger.info(f"Loading the content of {self.config_file}")
        try:
            with open(self.config_file) as jsonfile:
                self.config = json.load(jsonfile)
        except Exception as e:
            self.logger.error(f"An error occurred while loading the file. Fix the error and restart this application\n: {e}")
            return
        if not ergastirio.experiment_initializer.setup(self):
            return

    @property
    def refresh_time_internal_trigger(self):
        return self._refresh_time_internal_trigger
    @refresh_time_internal_trigger.setter
    def refresh_time_internal_trigger(self,r):
        try: 
            r = float(r)
            if self._refresh_time_internal_trigger == r: #in this case the number in the refresh time edit box is the same as the refresh time currently stored
                return True
        except ValueError:
            self.logger.error(f"The refresh time must be a valid number.")
            return self._refresh_time_internal_trigger
        if r < 0.001:
            self.logger.error(f"The refresh time must be positive and >= 1ms.")
            return self._refresh_time_internal_trigger
        self.logger.info(f"The refresh time (for internal trigger) is now {r} s.")
        self._refresh_time_internal_trigger = r
        return self._refresh_time_internal_trigger

    @property
    def refresh_time_multiple_acquisitions(self):
        return self._refresh_time_multiple_acquisitions
    @refresh_time_multiple_acquisitions.setter
    def refresh_time_multiple_acquisitions(self,r):
        try: 
            r = float(r)
            if self._refresh_time_multiple_acquisitions == r: #in this case the number in the refresh time edit box is the same as the refresh time currently stored
                return True
        except ValueError:
            self.logger.error(f"The refresh time must be a valid number.")
            return self._refresh_time_multiple_acquisitions
        if r < 0.001:
            self.logger.error(f"The refresh time must be positive and >= 1ms.")
            return self._refresh_time_multiple_acquisitions
        self.logger.info(f"The refresh time (for multiple acquisitions) is now {r} s.")
        self._refresh_time_multiple_acquisitions = r
        return self.refresh_time_multiple_acquisitions

    @property
    def numb_acquisitions_per_trigger(self):
        return self._numb_acquisitions_per_trigger
    @numb_acquisitions_per_trigger.setter
    def numb_acquisitions_per_trigger(self,n):
        try: 
            n = int(n)
            if self._numb_acquisitions_per_trigger == n:
                return True
        except ValueError:
            self.logger.error(f"The number of acquisitions per trigger must be a positive integer.")
            return self._numb_acquisitions_per_trigger
        if n < 1:
            self.logger.error(f"The number of acquisitions per trigger must be a positive integer.")
            return self._numb_acquisitions_per_trigger
        self.logger.info(f"The number of acquisitions per trigger is now {n}.")
        self._numb_acquisitions_per_trigger = n
        return self.numb_acquisitions_per_trigger

    def read_current_data_from_all_instruments(self):
        '''
        It looks into all the instruments interfaces (defined via the key 'interface' in each dictionary of the list exp.instruments) 
        and it extracts data from each instrument. From each instrument, the data to exctract is contained in the dictionary exp.instruments[i]['interface'].output
        '''
        current_data = []
        self.logger.info(f"Reading data from all instruments...")
        for instrument in self.instruments:        
            for data in instrument['interface'].output.values():
                current_data.append(data)  
        
        return current_data

    def store_current_data_from_all_instruments(self):
        '''
        '''
        current_data = self.read_current_data_from_all_instruments() #Read the current data from all instruments
        acq_numb = len(self.data) + 1 #We look at the number of rows of self.data
        now = datetime.datetime.now()
        time_string=now.strftime("%Y-%m-%d %H:%M:%S.%f")
        timestamp = datetime.datetime.timestamp(now)
        self.logger.info(f"[{time_string}] Acquisition #{acq_numb}")# {current_data}")
        current_data.insert(0, time_string)
        current_data.insert(0, timestamp )
        
        if ('PostProcessedData' in self.config.keys()):
            variables = {self.data_headers[i]: current_data[i] for i in range(len(current_data))}  #Create a dictionary with the values of the data that we just acquired
            for post_processed_data_name,post_processed_data_formula in self.config['PostProcessedData'].items():
                PostProcessedData = ergastirio.utils.evaluate_formula(post_processed_data_formula,variables)
                current_data.append(PostProcessedData)
        self.data.append(current_data)
        self.data_std.append([0]*(len(current_data)-2)) #Add a row of zeros to the standard deviations. The -2 is to avoid the columns corresponding to time and timestamp

    def set_trigger_modality(self,modality):
        if modality == 'internal':
            self.triggered_acquisition = False
            self.logger.info(f"Set the experiment to 'internal trigger modality'.")
        if modality == 'external':
            self.triggered_acquisition = True
            self.logger.info(f"Set the experiment to 'external trigger modality'.")

    def set_average_modality(self,modality):
        if modality == True:
            self.average_acquisition = True
            self.logger.info(f"Set averaged modality to True.")
        if modality == False:
            self.average_acquisition = False
            self.logger.info(f"Set averaged modality to False.")

    def take_single_acquisition(self):
        self.store_current_data_from_all_instruments()

    def take_single_set_of_acquisitions(self,counter):
        ''' Takes a sequence of acquisitions. The number of acquisitions is counter, separated by a time self.refresh_time_multiple_acquisitions.
            This function calls take_single_acquisition() and then calls itself after a time specified by self.refresh_time_multiple_acquisitions, 
            and with counter = counter -1.
            Normally, this function is called by another function with the input argument counter = self.numb_acquisitions_per_trigger
        '''
        self.take_single_acquisition()
        if counter > 1: #if there are more acquisitions to take we call the function again
            QtCore.QTimer.singleShot(int(self.refresh_time_multiple_acquisitions*1e3), lambda: self.take_single_set_of_acquisitions(counter=counter-1))
        elif self.average_acquisition and self.numb_acquisitions_per_trigger>1:
            self.logger.info(f"Averaging the last {self.numb_acquisitions_per_trigger} acquisitions and calculating errors...")
            self.make_average_last_acquisitions()

    def make_average_last_acquisitions(self):
        '''
        Take the last N elements of self.data (where N = self.numb_acquisitions_per_trigger) and replace them with their average (column-wise)
        It also populates the standard deviations (TO DO)
        '''
        N = self.numb_acquisitions_per_trigger
        rows_to_average = self.data[-N:] #Get the last N rows
        timestamp = rows_to_average[0][0]
        time = rows_to_average[0][1]
        rows_to_average2 = [elem[2:] for elem in rows_to_average] #Remove first two columns, which is timestamp and time
        averaged = (np.nanmean(np.array(rows_to_average2),axis=0)).tolist()
        std = (np.nanstd(np.array(rows_to_average2),axis=0)).tolist()
        averaged.insert(0, time)
        averaged.insert(0, timestamp )
        del self.data[-N:]      #Remove last N rows from data
        del self.data_std[-N:]  #Remove last N rows from data_std
        self.data.append(averaged)
        self.data_std.append(std)

    def trigger_single_set_acquisition(self):
        self.take_single_set_of_acquisitions(counter=self.numb_acquisitions_per_trigger)

    def update(self):
        '''
        If we are doing a continuous acquisition, it calls self.store_current_data_from_all_instruments(). If we are not in external triggered modality, it calls
        itself after a time equal to int(self.refresh_time_internal_trigger*1e3) (in ms)
        '''
        if self.continous_acquisition:
            self.take_single_set_of_acquisitions(counter=self.numb_acquisitions_per_trigger)
            if self.continous_acquisition == True and self.triggered_acquisition  == False:
                QtCore.QTimer.singleShot(int(self.refresh_time_internal_trigger*1e3), self.update)  
                
    def start_continous_acquisition(self):
        self.continous_acquisition = True
        if self.triggered_acquisition == True:
            self.logger.info(f"Waiting for next trigger from {self.trigger_instrument}...")
        else:
            self.update()
        return

    def stop_continous_acquisition(self):
        self.continous_acquisition = False

    def trigger(self):
        '''
        This function is called by instruments if they are set as trigger and when they fire a trigger
        '''
        if self.continous_acquisition:
            if self.triggered_acquisition:
                self.logger.info(f"Received trigger from {self.trigger_instrument}...")
                self.update()
                self.logger.info(f"Waiting for next trigger from {self.trigger_instrument}...")
            else:
                self.logger.info(f"Received a trigger from {self.trigger_instrument}, but experiment is not in 'external trigger' modality.")
        else:
            self.logger.info(f"Received a trigger from {self.trigger_instrument}, but experiment is not currently acquiring data.")

    def set_trigger_instrument(self,instrument_name,delay):
        try: 
            delay = float(delay)
        except ValueError:
            self.logger.error(f"The trigger must be a valid number.")
            return False
        if delay < 0:
            self.logger.error(f"The delay time must be positive and >= 1ms.")
            return False
        if (self.trigger_instrument == instrument_name) and (self.trigger_delay == delay): #in this case the number in the refresh time edit box is the same as the refresh time currently stored
            return True
        self.trigger_instrument = ''
        self.logger.info(f"Setting the instrument {instrument_name} as trigger, with delay {delay}...")
        for instrument in self.instruments:        
            if instrument['fullname'] == instrument_name:
                try:
                    instrument['interface'].set_trigger(self.trigger,delay=delay)
                    self.trigger_instrument = instrument_name
                    self.trigger_delay = delay
                except Exception as e:
                    self.logger.error(f"An error occurred while setting {self.trigger_instrument} as trigger:\n {e}")
                    return False
            else: #we set the trigger of this instrument to None
                try:
                    instrument['interface'].set_trigger(None,delay=delay)
                except Exception as e:
                    self.logger.error(f"{e}")
        if self.trigger_instrument == '':
            self.logger.error(f"There is not an instrument called {instrument_name}")
            return False
        self.logger.info(f"{self.trigger_instrument} was succesfully set as trigger.")
        return True

    def delete_current_data(self):
        self.logger.info(f"All store data was deleted.")
        self.data.clear()
        self.data_std.clear()

    def delete_row_from_data(self,row):
        try:
            self.data.pop(row)
            self.data_std.pop(row)
            if row == -1:
                row = 'Last'
            self.logger.info(f"{row} row has been removed from data.")
        except:
            pass

    def save_stored_data(self,filename):
        '''
        Saves the values of all currently stored data on file. 
        The data are saved in a tabular form and delimited by a comma.
        '''
        d =','
        header = ''
        for h in self.data_headers:
            header = header + h + d 
        for h in self.data_headers: #We skip the first element of headers which corresponds to acquisition time
            if h not in ['timestamp', 'time']: #This avoids generating the headers timestamp_std and time_std
                header = header + (h+'_std') +  d

        A = np.concatenate((np.array(self.data), np.array(self.data_std)),axis=1)
        print(A)
        np.savetxt(filename, A, delimiter=d, header=header, comments="",fmt='%s')#,fmt=d.join(['%s'] + ['%e']*(A.shape[1]-1)))
        self.logger.info(f"Saved all stored data (number of rows = {A.shape[0]} in the file {filename}")
        return

    def close_experiment(self):
        for instrument in self.instruments:
            try:
                instrument['interface'].close()
            except:
                pass

class EnhancedList(list):
    '''
    This class is used to generate an "event-based" list object. Everytime the content of the list changes, it also stores a copy of the list 
    in a certain property of all the objects specified in the list linked_objects. 
    Each element of linked_objects is a two-element list in the form [class_instance,class_property]. This behavior is useful when the linked objects
    are, e.g., plots and tables, and the targeted property is defined via a @setter, in order to automatically update parts of the gui

    Examples:

        class test():
            def __init__( self ):
                self.__value = "old value"

            @property
            def value( self ):
                return self.__value

            @value.setter
            def value( self, value ):
                self.__value = value
                print("Targeted list changed to " + str(value))

        a = EnhancedList([1,2,3])
        t=test()
        a.add_syncronized_objects([t,test.value])
        a.append(4)

    Targeted list changed to [1, 2, 3, 4]

    '''
    

    def __init__(self,  *args):
        self.linked_objects = []

    def add_syncronized_objects(self,list_objects):
        self.linked_objects.append(list_objects)

    def sync(self):
        for obj in self.linked_objects:
            obj[1].fset(obj[0], self.copy())

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.sync()
    def __delitem__(self, value):
        super().__delitem__(value)
        self.sync()
    def __add__(self, value):
        super().__add__(value)
        self.sync()
    def __iadd__(self, value):
        super().__iadd__(value)
        self.sync()
    def append(self, value):
        super().append(value)
        self.sync()
    def remove(self, value):
        super().remove(value)
        self.sync()
    def insert(self, *args):
        super().insert(*args)
        self.sync()
    def pop(self, *args):
        super().pop(*args)
        self.sync()
    def clear(self):
        super().clear()
        self.sync()