import configparser

import os
import time

import ctypes
import threading

import shutil

import wx
import wx.adv
import wx.lib.newevent

try:
    from extraction import *
except:
    from huellas.extraction import *

try:
    from segmentation import *
except:
    from huellas.segmentation import *

try:
    from auxiliar import *
except:
    from huellas.auxiliar import *

ThreadFinishEvent, EVT_THREAD_FINISH_EVENT = wx.lib.newevent.NewEvent()
ThreadUpdateEvent, EVT_THREAD_UPDATE_EVENT = wx.lib.newevent.NewEvent()
ThreadRefreshEvent, EVT_THREAD_REFRESH_EVENT = wx.lib.newevent.NewEvent()
ThreadCleanEvent, EVT_THREAD_CLEAN_EVENT = wx.lib.newevent.NewEvent()

class TimerThread(threading.Thread):

    def __init__(self, step_milliseconds, dialog, *args, **kwargs):
        super(TimerThread, self).__init__(*args, **kwargs)

        self.step_milliseconds = step_milliseconds
        self.dialog = dialog
        self.stopped = False

    def run(self):
        evt = ThreadRefreshEvent()
        while not self.stopped:
            time.sleep(self.step_milliseconds / 1000)
            try:
                wx.PostEvent(self.dialog, evt)
            except RuntimeError as e:
                self.stop()
        
    def stop(self):
        self.stopped = True


class ProcessingThread(threading.Thread):

    def __init__(self, input_img_path, output_folder_path, dialog, BORDER_OFFSET=100, *args, **kwargs):
        super(ProcessingThread, self).__init__(*args, **kwargs)
        
        self.filename = input_img_path.split(os.sep)[-1]
        self.file_head, self.file_ext = self.filename.split(".")
        
        output_folder_path += os.sep + self.file_head + os.sep

        self.input_img_path = input_img_path
        self.output_folder_path = output_folder_path
        self.dialog = dialog
        self.BORDER_OFFSET = BORDER_OFFSET

        self.blob_map_path = None
        self.fprints_paths = []
        self.is_aborted = False
 
    def abort(self):
        self.is_aborted = True

    def get_extracted_paths(self):
        return self.blob_map_path, self.fprints_paths

    def update_event(self, step_size, message):
        evt = ThreadUpdateEvent(step_size=step_size, message=message)
        wx.PostEvent(self.dialog, evt)

    def read_paths_from_config(self):
        processed_ini_path = self.output_folder_path + ".processed.ini"
        processed_ini_config = configparser.ConfigParser()
        processed_ini_config.read(processed_ini_path)
        for key in processed_ini_config[self.filename]:
            if "blob" in key:
                self.blob_map_path = processed_ini_config[self.filename][key]
            elif "fprin" in key:
                self.fprints_paths.append(processed_ini_config[self.filename][key])
        self.fprints_paths.sort()

    def create_config_file(self):
        processed_ini_path = self.output_folder_path + ".processed.ini" 
        if os.path.exists(processed_ini_path):
            os.remove()
        processed_ini_config = configparser.ConfigParser()
        processed_ini_config[self.filename] = {}
        # Blob map path
        processed_ini_config[self.filename][self.blob_map_path.split(".")[0]] = self.blob_map_path
        # Fprint paths
        for path in self.fprints_paths:
            processed_ini_config[self.filename][path.split(".")[0]] = path

        with open(processed_ini_path, "w") as fp:
            processed_ini_config.write(fp)

    def finish_event(self):
        evt = ThreadFinishEvent()
        wx.PostEvent(self.dialog, evt)

    def clean_event(self):
        evt = ThreadCleanEvent()
        wx.PostEvent(self.dialog, evt)

    def run(self):
        try:
            self.read_paths_from_config()
            self.clean_event()
            self.finish_event()
            return
        except Exception as e:
            #print(e)
            #import ipdb;ipdb.set_trace()
            pass
        
        input_img_path = self.input_img_path
        output_folder_path = self.output_folder_path
        BORDER_OFFSET = self.BORDER_OFFSET

        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        # Load and do inital processing
        original, grayscale, preprocessed = load_and_preprocess_image(input_img_path)
        self.update_event(6, "Calculating shape...")

        if self.is_aborted : return ;

        # Get image height/width
        img_height, img_width = grayscale.shape
        self.update_event(6, "Adaptive binarization...")
        
        if self.is_aborted : return ;

        bin_image = adaptive_threshold(preprocessed)
        self.update_event(6, "Removing scan borders...")
        
        if self.is_aborted : return ;

        noborder_bin_image = remove_border_lines(bin_image)
        self.update_event(6, "Calculating superpixel segmentation...")
        
        if self.is_aborted : return ;

        superpixel_mask = superpixel_segmentation(noborder_bin_image) 
        self.update_event(6, "Cleaning superpixel binarization...")
        
        if self.is_aborted : return ;

        noartifacts_superpixel_mask = clean_artifacts(superpixel_mask)
        self.update_event(6, "Closing spaces between regions...")
        
        if self.is_aborted : return ;

        clean_mask = connect_close_blobs(noartifacts_superpixel_mask)
        self.update_event(6, "Calculating connected components...")
        
        if self.is_aborted : return ;

        # Map connected components in clean image
        qty, label_mask, label_counts = connected_components(clean_mask)
        self.update_event(6, "Producing component visualization...")
        
        if self.is_aborted : return ;

        # Color connected components for visualization
        clean_blobs_color = colorear_componentes_conexas(label_mask)
        self.update_event(6, "Building region representation...")
        
        if self.is_aborted : return ;

        # Transform components to Region objects
        regions = build_region_objects(label_counts, label_mask, grayscale)
        self.update_event(6, "Saving visualization...")
        
        if self.is_aborted : return ;

        # Number regions in color image and save
        for i, region in regions:
            cv2.putText(clean_blobs_color,
                        str(i),
                        region.centroid,
                        cv2.FONT_HERSHEY_COMPLEX,
                        1, (255, 255, 255), 2)
        guardar_imagen(clean_blobs_color, output_folder_path + "blob_numbers.png")
        self.blob_map_path = output_folder_path + "blob_numbers.png"
        self.update_event(6, "Detecting fingerprints...")
        
        if self.is_aborted : return ;

        # Get isolated fingerprint candidates
        border_height = int(grayscale.shape[0]/4)
        border_width = int(grayscale.shape[1]/4)
        f_candidates, final_candidate_labels = get_fingerprint_candidates(
                regions, 
                border_height, 
                border_width, 
                img_height,
                img_width)
        self.update_event(6, "Saving detected fingerprints...")
        
        if self.is_aborted : return ;

        # Save remaining fingerprint candidates
        self.fprints_paths = save_fingerprint_candidates(
                f_candidates, 
                final_candidate_labels, 
                output_folder_path)
        self.update_event(6, "Detecting hand(s)...")
        
        if self.is_aborted : return ;

        # For every non-candidate, assume it may be part of a hand
        hand_candidates, hand_region_coordinates = get_hand_candidates(
                regions,
                final_candidate_labels,
                img_height,
                img_width,
                BORDER_OFFSET)
        self.update_event(6, "Cleaning hand region...")
        
        if self.is_aborted : return ;

        # Remove non-candidate regions from final mask
        remove_noncandidate_regions_from_mask(
                regions, 
                hand_candidates, 
                noartifacts_superpixel_mask)
        self.update_event(6, "Extracting hand(s)...")
        
        if self.is_aborted : return ;

        extracted_hand, hand_label_mask = extract_hand(
                noborder_bin_image,
                noartifacts_superpixel_mask,
                hand_region_coordinates,
                original)
        self.update_event(6, "Adding alpha channel...")
        
        if self.is_aborted : return ;

        extracted_hand_alpha = add_alpha_channel(extracted_hand, hand_label_mask)
        self.update_event(6, "Saving hand(s)...")

        if self.is_aborted : return ;
        
        # Save hand
        cv2.imwrite(output_folder_path + "hand0.png", extracted_hand_alpha)
        
        self.update_event(6, "Finished!")
        self.create_config_file()
        self.finish_event()


class ProcessingProgressDialog(wx.ProgressDialog):

    def __init__(self, path_to_image, output_folder):
        self.filename = path_to_image.split(os.sep)[-1]
        self.file_head, self.file_ext = self.filename.split(".")
        super(ProcessingProgressDialog, self).__init__(
                "Processing " + self.filename,
                "Loading file...", 
                100,
                style=wx.PD_APP_MODAL|wx.PD_AUTO_HIDE|wx.PD_ELAPSED_TIME|wx.PD_CAN_ABORT)

        self.last_value = 0
        self.last_message = "Loading file..."

        self.Bind(EVT_THREAD_UPDATE_EVENT, self.update)
        self.Bind(EVT_THREAD_REFRESH_EVENT, self.refresh)
        self.Bind(EVT_THREAD_FINISH_EVENT, self.finish)
        self.Bind(EVT_THREAD_CLEAN_EVENT, self.clean)

        self.main_thread = ProcessingThread(path_to_image, output_folder, self)
        self.main_thread.start()

        self.refresh_thread = TimerThread(1000, self)
        self.refresh_thread.start()

        self.aborted = False

    def last_update(self):
        self.last_value = 100
        self.last_message = "Finished!"

    def update(self, e):
        self.last_value = min(self.last_value + e.step_size, 100)
        self.last_message = e.message

    def clean(self, e):
        self.last_update()
        self.Update(self.last_value, self.last_message)

    def refresh(self, e):
        self.Update(self.last_value, self.last_message)
        if self.WasCancelled():
            self.refresh_thread.stop()
            self.refresh_thread.join()
            self.Resume()
            self.Update(self.last_value, "Aborting...")
            self.main_thread.abort()
            self.main_thread.join()
            shutil.rmtree(self.main_thread.output_folder_path)
            self.aborted = True
            self.Update(100, "Finished!")

    def finish(self, e):
        self.refresh_thread.stop()


class ProcessingFolderProgressDialog(wx.ProgressDialog):

    def __init__(self, path_to_folder, output_folder):
        
        if not path_to_folder.endswith(os.sep):
            path_to_folder += os.sep

        self.files_to_process = []
        for f in os.listdir(path_to_folder):
            if f.endswith(".jpg") or f.endswith(".png") or f.endswith(".jpeg"):
                self.files_to_process.append(path_to_folder + f)

        # Current file is the 0th
        self.current = 0
       
        self.max_value = len(self.files_to_process) * 100 

        self.filename = self.get_current_path().split(os.sep)[-1]
        self.file_head, self.file_ext = self.filename.split(".")

        # Create the actual dialog        
        super(ProcessingFolderProgressDialog, self).__init__(
                "Processing folder ({0})".format(self.filename),
                "Loading files...", 
                self.max_value,
                style=wx.PD_APP_MODAL|wx.PD_AUTO_HIDE|wx.PD_ELAPSED_TIME|wx.PD_CAN_ABORT)

        self.last_value = 0
        self.last_message = "Loading file {0}...".format(self.filename)

        self.Bind(EVT_THREAD_UPDATE_EVENT, self.update)
        self.Bind(EVT_THREAD_REFRESH_EVENT, self.refresh)
        self.Bind(EVT_THREAD_FINISH_EVENT, self.finish)
        self.Bind(EVT_THREAD_CLEAN_EVENT, self.clean)
        
        # Start refreshing thread
        self.refresh_thread = TimerThread(1000, self)
        self.refresh_thread.start()

        # Create per-file threads
        self.main_threads = []
        for i in range(len(self.files_to_process)):
            thrd = ProcessingThread(self.files_to_process[i], output_folder, self)
            self.main_threads.append(thrd)

        # Start first thread
        self.main_thread = self.get_current_thread() 
        self.main_thread.start()

        self.aborted = False

    def get_current_path(self):
        return self.files_to_process[self.current]

    def get_current_thread(self):
        return self.main_threads[self.current]

    def last_update(self):
        self.last_value = self.max_value
        self.last_message = "Finished!"

    def update(self, e):
        self.last_value = min(self.last_value + e.step_size, self.max_value)
        self.last_message = e.message

    def clean(self, e):
        self.last_value = min(self.last_value + 100, self.max_value)
        self.last_message = "Finished!"

    def refresh(self, e):
        self.Update(self.last_value, self.last_message)
        if self.WasCancelled():
            self.refresh_thread.stop()
            self.Resume()
            self.Update(self.last_value, "Aborting...")
            self.main_thread.abort()
            self.main_thread.join()
            shutil.rmtree(self.main_thread.output_folder_path)
            self.aborted = True
            self.last_update()
            self.Update(self.last_value, self.last_message)

    def finish(self, e):
        if self.current + 1 < len(self.files_to_process):
            self.current += 1
            self.filename = self.get_current_path().split(os.sep)[-1]
            self.file_head, self.file_ext = self.filename.split(".")
            self.last_message = "Loading file {0}...".format(self.filename)
            self.SetTitle("Processing folder ({0})".format(self.filename))
            self.main_thread.join()
            self.main_thread = self.get_current_thread()
            self.main_thread.start()
        else:
            self.refresh_thread.stop()
            self.main_thread.join()
