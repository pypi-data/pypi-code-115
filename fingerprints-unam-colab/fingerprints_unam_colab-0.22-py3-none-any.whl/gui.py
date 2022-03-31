import configparser

import math

import wx
import wx.adv
import os

from pathlib import Path

try: 
    from gui_processing import ProcessingProgressDialog, ProcessingFolderProgressDialog
except:
    from huellas.gui_processing import ProcessingProgressDialog, ProcessingFolderProgressDialog

LOAD_ITEM = 1
LOAD_FOLDER_ITEM = 2
EXIT_ITEM = 3


class FingerprintMainFrame(wx.Frame):

    def __init__(self, config, parent=None, title="Main"):
        super(FingerprintMainFrame, self).__init__(parent, title=title)

        self.config = config
       
        self.last_folder_opened = os.path.expanduser("~")

        self.last_panel = None

        # Window size/position
        self.SetSize((1024, 768))
        self.Centre()

        # Prepare menu bar
        self.configure_menu()
        
        # Prepare internal layout
        self.configure_layout()

        # Close events
        self.Bind(wx.EVT_CHAR_HOOK, self.close_on_key)
        self.Bind(wx.EVT_CLOSE, self.destroy)
        self.Show(True)

    def configure_menu(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        #file_item = file_menu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        
        load_item = wx.MenuItem(file_menu, LOAD_ITEM, '&Load image\tCtrl+L')
        self.Bind(wx.EVT_MENU, self.load_image, id=LOAD_ITEM)
        file_menu.Append(load_item)
        
        load_folder_item = wx.MenuItem(file_menu, LOAD_FOLDER_ITEM, '&Load folder\tCtrl+F')
        self.Bind(wx.EVT_MENU, self.load_folder, id=LOAD_FOLDER_ITEM)
        file_menu.Append(load_folder_item)

        quit_item = wx.MenuItem(file_menu, EXIT_ITEM, '&Quit\tCtrl+Q')
        #quit_item.SetBitmap(wx.Bitmap('exit.png'))
        self.Bind(wx.EVT_MENU, self.close, id=EXIT_ITEM)
        file_menu.Append(quit_item)
        
        menubar.Append(file_menu, '&File')

        self.SetMenuBar(menubar)

    def resize_image(self, img, max_width=None, max_height=None):
        width, height = img.GetSize()
        pwidth, pheight = self.GetSize()

        if max_width == None:
            max_width = pwidth
        if max_height == None:
            max_height = pheight

        if width > max_width:
            percentage = (width / max_width)
            new_width = int(width/percentage)
            new_height = int(height/percentage)
        else:
            new_width = width
            new_height = height
        
        if new_height > max_height:
            percentage = (new_height / max_height)
            new_width = int(new_width/percentage)
            new_height = int(new_height/percentage)
       
        img.Rescale(new_width, new_height)
        return img

    def configure_layout(self, blob_map_path=None, fprint_paths=None, deactivated_buttons=True):
        if blob_map_path == None:
            blob_map_path = self.config["DEFAULT"]["image_dir"] + os.sep + "mpipimi.png"
        if fprint_paths == None:
            fprint_paths = []
            for i in range(8):
                fprint_paths.append(self.config["DEFAULT"]["image_dir"] + os.sep + "popuko.png")
        if self.last_panel != None:
            self.last_panel.Destroy()

        panel = wx.Panel(self, style=wx.EXPAND)
        #panel.SetBackgroundColour("#ff0000")

        # Main container
        hbox = wx.BoxSizer(wx.HORIZONTAL) 

        # Load and Resize
        # Size maximums
        pwidth, pheight = self.GetSize()
        max_width = int(pwidth/2)
        
        # Vertical resize depending on qty of rows
        # max_rows + 1 (for extra elements)
        max_rows = math.ceil(len(fprint_paths) / 2) 
        max_height = int(pheight/(max_rows + 1))

        # Resize blob img
        large_img = wx.Image(blob_map_path,
                             wx.BITMAP_TYPE_ANY)
        large_img = self.resize_image(large_img, max_width)
        
        small_imgs = []
        for i in range(len(fprint_paths)):
            small_img = wx.Image(fprint_paths[i], wx.BITMAP_TYPE_ANY)
            small_img = self.resize_image(small_img, max_width, max_height)
            small_imgs.append(small_img)

        # Assign blobs to container in panel
        blobs_box = wx.BoxSizer(wx.VERTICAL)
        large_bmp = large_img.ConvertToBitmap()
        img = wx.StaticBitmap(panel, bitmap=large_bmp, size=large_bmp.GetSize())
        blobs_box.Add(img, flag=wx.EXPAND, border=10)

        # Assign fprints  to container in panel
        fprints_box1 = wx.BoxSizer(wx.VERTICAL)
        fprints_box2 = wx.BoxSizer(wx.VERTICAL)
        for i in range(len(fprint_paths)):
            small_bmp = small_imgs[i].ConvertToBitmap()
        
            button = wx.BitmapButton(panel, 
                                     bitmap=small_bmp,
                                     size=small_bmp.GetSize())
            if deactivated_buttons:
                button.Disable()
            if i < max_rows:
                fprints_box1.Add(button, border=10)
            else:
                fprints_box2.Add(button, border=10)

        # Add sub-containers to main container
        hbox.Add(blobs_box)
        hbox.Add(fprints_box1, border=10)
        hbox.Add(fprints_box2, border=10)
       
        # Set main container to panel
        panel.SetSizer(hbox)
        self.last_panel = panel

        # TODO: Find the correct way to update
        self.SetSize((pwidth + 1, pheight + 1))
        self.SetSize((pwidth - 1, pheight - 1))

    def close_on_key(self, e):
        keycode = e.GetKeyCode()
        if keycode == wx.WXK_ESCAPE or keycode==27:
            self.close(e)

    def load_image(self, e):
        '''Load image file for processing'''

        # Load file
        with wx.FileDialog(self, 
                "Open handprint image file", 
                defaultDir=self.last_folder_opened,
                wildcard="Image files (*.bmp;*.jpg;*.jpeg;*.png)|*.bmp;*.jpg;*.jpeg;*.png",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return     # the user clicked "Cancel"

            # Else get the actual file
            pathname = file_dialog.GetPath()

            # Refresh folder memory
            self.last_folder_opened = os.sep.join(pathname.split(os.sep)[:-1])

            # Open processing dialog / process
            processing_dialog = ProcessingProgressDialog(
                    pathname, 
                    self.config["DEFAULT"]["output_dir"])

            processing_dialog.Bind(wx.EVT_SHOW, self.finished_processing)

    def load_folder(self, e):

        # Load file
        with wx.DirDialog(self, 
                "Open folder with handprints",
                defaultPath=self.last_folder_opened,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return     # the user clicked "Cancel"

            # Else get the actual file
            pathname = file_dialog.GetPath()
            
            # Refresh folder memory
            self.last_folder_opened = os.sep.join(pathname.split(os.sep)[:-1])

            # Open processing dialog / process
            processing_dialog = ProcessingFolderProgressDialog(
                    pathname, 
                    self.config["DEFAULT"]["output_dir"])

            processing_dialog.Bind(wx.EVT_SHOW, self.finished_processing)
    
    # TODO: Do it here instead of the thread's corpse
    def finished_processing(self, e):
        dialog = e.GetEventObject()
        if not dialog.aborted:
            self.SetTitle(dialog.main_thread.filename)
            #if dialog.main_thread.blob_map_path == None:
            #    import ipdb;ipdb.set_trace()
            #print(dialog.main_thread.blob_map_path)
            #print(dialog.main_thread.fprints_paths)
            self.configure_layout(dialog.main_thread.blob_map_path, dialog.main_thread.fprints_paths, False)

    def close(self, e):
        self.Close(True)
        e.Skip()

    def destroy(self, e):
        self.Destroy()


class FingerprintSplash(wx.adv.SplashScreen):

    def __init__(self, images_dir):
        splash_logo = wx.Bitmap(images_dir + os.sep + "splash.png")
        super(FingerprintSplash, self).__init__(
                splash_logo,
                wx.adv.SPLASH_CENTER_ON_SCREEN|wx.adv.SPLASH_TIMEOUT,
                2000, None)

        self.Bind(wx.EVT_CLOSE, self.splash_disappears)
        wx.BeginBusyCursor()
    
    def splash_disappears(self, e):
        e.Skip()
        wx.CallAfter(wx.EndBusyCursor)
        self.Destroy()


class FingerprintApp(wx.App):

    def OnInit(self):
        
        self.user_folder = os.path.expanduser("~")
        self.configuration_file_path = self.user_folder + os.sep + ".fingerprint_config.ini"
        self.config = configparser.ConfigParser()
        
        try:
            # Load configuration
            self.config.read(self.configuration_file_path)
            self.base_dir = self.config["DEFAULT"]["base_dir"]
            self.resource_dir = self.config["DEFAULT"]["resource_dir"]
            self.image_dir = self.config["DEFAULT"]["image_dir"]
        except Exception as e:
            # Create configuration file
            self.config["DEFAULT"] = {}
            
            self.base_dir = os.path.abspath(__file__).split(os.sep)[:-1]
            self.base_dir = os.sep.join(self.base_dir)
            
            self.resource_dir = self.base_dir + os.sep + "resources"
    
            self.image_dir = self.resource_dir + os.sep + "images"
            
            self.config["DEFAULT"]["base_dir"] = self.base_dir
            self.config["DEFAULT"]["resource_dir"] = self.resource_dir
            self.config["DEFAULT"]["image_dir"] = self.image_dir

            self.save_config_file()
    
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        self.SetAppName("Fingerprint extraction")
        
        self.app_splash = FingerprintSplash(self.image_dir)
        self.app_splash.Bind(wx.EVT_WINDOW_DESTROY, self.splash_disappears)
        self.app_splash.Show(True)
        
        return True
    
    def save_config_file(self):
        with open(self.configuration_file_path, "w") as fp:
            self.config.write(fp)

    def splash_disappears(self, e):
        e.Skip()
        self.show_next_dialog()
   
    def show_next_dialog(self):
        show_main_frame = False
        try:
            # Check if output config is present
            self.output_dir = self.config['DEFAULT']['output_dir']
            show_main_frame = True
        except:
            pass

        if show_main_frame:
            self.show_main_frame()
        else:
            self.show_configuration_dialog()

    def show_configuration_dialog(self):
        # Load file
        with wx.DirDialog(None, 
                "Select output folder (results will be put there)",
                defaultPath=self.user_folder,
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                self.ExitMainLoop()
                return     # the user clicked "Cancel"

            # Else get the actual file
            pathname = file_dialog.GetPath()
            self.config["DEFAULT"]["output_dir"] = pathname
            self.save_config_file()
        self.show_main_frame()

    def show_main_frame(self):
        main_frame = FingerprintMainFrame(self.config, 
                                          title="Fingerprint extraction")


def entry_point():
    app = FingerprintApp(False)
    app.MainLoop()


if __name__ == "__main__":
    entry_point()
