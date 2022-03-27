#! python3
# -*- coding: utf-8 -*-
"""mwxlib framework

Author: Kazuya O'moto <komoto@jeol.co.jp>
"""
__version__ = "0.54.9"
__author__ = "Kazuya O'moto <komoto@jeol.co.jp>"

from functools import partial
from functools import wraps
import traceback
import datetime
import keyword
import shlex
import time
import sys
import os
import re
import wx
from wx import aui
from wx import stc
from wx.py import dispatcher
from wx.py.shell import Shell
from wx.py.editwindow import EditWindow
import pydoc
import linecache
import inspect
from pprint import pprint, pformat
from six.moves import builtins
from six import string_types
from importlib import reload
try:
    import utilus as ut
    from utilus import (FSM, TreeList, funcall, wdir,
                        apropos, typename, where, mro, pp,)
except ImportError:
    from . import utilus as ut
    from .utilus import (FSM, TreeList, funcall, wdir,
                         apropos, typename, where, mro, pp,)

_F = funcall


speckeys = {
    wx.WXK_ALT                  : 'alt',
    wx.WXK_BACK                 : 'backspace',
    wx.WXK_CANCEL               : 'break',
    wx.WXK_CAPITAL              : 'caps_lock',
    wx.WXK_CONTROL              : 'ctrl',
    wx.WXK_DELETE               : 'delete',
    wx.WXK_DOWN                 : 'down',
    wx.WXK_END                  : 'end',
    wx.WXK_ESCAPE               : 'escape',
    wx.WXK_F1                   : 'f1',
    wx.WXK_F2                   : 'f2',
    wx.WXK_F3                   : 'f3',
    wx.WXK_F4                   : 'f4',
    wx.WXK_F5                   : 'f5',
    wx.WXK_F6                   : 'f6',
    wx.WXK_F7                   : 'f7',
    wx.WXK_F8                   : 'f8',
    wx.WXK_F9                   : 'f9',
    wx.WXK_F10                  : 'f10',
    wx.WXK_F11                  : 'f11',
    wx.WXK_F12                  : 'f12',
    wx.WXK_F13                  : 'f13',
    wx.WXK_F14                  : 'f14',
    wx.WXK_F15                  : 'f15',
    wx.WXK_F16                  : 'f16',
    wx.WXK_F17                  : 'f17',
    wx.WXK_F18                  : 'f18',
    wx.WXK_F19                  : 'f19',
    wx.WXK_F20                  : 'f20',
    wx.WXK_F21                  : 'f21',
    wx.WXK_F22                  : 'f22',
    wx.WXK_F23                  : 'f23',
    wx.WXK_F24                  : 'f24',
    wx.WXK_HOME                 : 'home',
    wx.WXK_INSERT               : 'insert',
    wx.WXK_LEFT                 : 'left',
    wx.WXK_NONE                 : 'none',
    wx.WXK_NUMLOCK              : 'num_lock',
    wx.WXK_NUMPAD_ADD           : '+',
    wx.WXK_NUMPAD_DECIMAL       : 'dec',
    wx.WXK_NUMPAD_DELETE        : 'delete',
    wx.WXK_NUMPAD_DIVIDE        : '/',
    wx.WXK_NUMPAD_DOWN          : 'down',
    wx.WXK_NUMPAD_END           : 'end',
    wx.WXK_NUMPAD_ENTER         : 'enter',
    wx.WXK_NUMPAD_HOME          : 'home',
    wx.WXK_NUMPAD_INSERT        : 'insert',
    wx.WXK_NUMPAD_LEFT          : 'left',
    wx.WXK_NUMPAD_MULTIPLY      : '*',
    wx.WXK_NUMPAD_PAGEDOWN      : 'pagedown',
    wx.WXK_NUMPAD_PAGEUP        : 'pageup',
    wx.WXK_NUMPAD_RIGHT         : 'right',
    wx.WXK_NUMPAD_SUBTRACT      : '-',
    wx.WXK_NUMPAD_UP            : 'up',
    wx.WXK_NUMPAD0              : '0',
    wx.WXK_NUMPAD1              : '1',
    wx.WXK_NUMPAD2              : '2',
    wx.WXK_NUMPAD3              : '3',
    wx.WXK_NUMPAD4              : '4',
    wx.WXK_NUMPAD5              : '5',
    wx.WXK_NUMPAD6              : '6',
    wx.WXK_NUMPAD7              : '7',
    wx.WXK_NUMPAD8              : '8',
    wx.WXK_NUMPAD9              : '9',
    wx.WXK_PAGEDOWN             : 'pagedown',
    wx.WXK_PAGEUP               : 'pageup',
    wx.WXK_PAUSE                : 'break',
    wx.WXK_RETURN               : 'enter',
    wx.WXK_RIGHT                : 'right',
    wx.WXK_SCROLL               : 'scroll_lock',
    wx.WXK_SHIFT                : 'shift',
    wx.WXK_SNAPSHOT             : 'snapshot',
    wx.WXK_SPACE                : 'space',
    wx.WXK_TAB                  : 'tab',
    wx.WXK_UP                   : 'up',
    wx.WXK_WINDOWS_LEFT         : 'Lwin',
    wx.WXK_WINDOWS_MENU         : 'appskey',
    wx.WXK_WINDOWS_RIGHT        : 'Rwin',
    ## wx.WXK_CONTROL_A            : 'a',
    ## wx.WXK_CONTROL_B            : 'b',
    ## wx.WXK_CONTROL_C            : 'c',
    ## wx.WXK_CONTROL_D            : 'd',
    ## wx.WXK_CONTROL_E            : 'e',
    ## wx.WXK_CONTROL_F            : 'f',
    ## wx.WXK_CONTROL_G            : 'g',
    ## wx.WXK_CONTROL_H            : 'h', # 8=WXK_BACK (C-h)
    ## wx.WXK_CONTROL_I            : 'i', # 9=WXK_TAB (C-i)
    ## wx.WXK_CONTROL_J            : 'j',
    ## wx.WXK_CONTROL_K            : 'k',
    ## wx.WXK_CONTROL_L            : 'l',
    ## wx.WXK_CONTROL_M            : 'm', # 13=WXK_RETURN (C-m)
    ## wx.WXK_CONTROL_N            : 'n',
    ## wx.WXK_CONTROL_O            : 'o',
    ## wx.WXK_CONTROL_P            : 'p',
    ## wx.WXK_CONTROL_Q            : 'q',
    ## wx.WXK_CONTROL_R            : 'r',
    ## wx.WXK_CONTROL_S            : 's',
    ## wx.WXK_CONTROL_T            : 't',
    ## wx.WXK_CONTROL_U            : 'u',
    ## wx.WXK_CONTROL_V            : 'v',
    ## wx.WXK_CONTROL_W            : 'w',
    ## wx.WXK_CONTROL_X            : 'x',
    ## wx.WXK_CONTROL_Y            : 'y',
    ## wx.WXK_CONTROL_Z            : 'z',
}

def speckey_state(key):
    k = next((k for k,v in speckeys.items() if v == key), None)
    if k:
        return wx.GetKeyState(k) #cf. wx.GetMouseState


def hotkey(evt):
    """Interpret evt.KeyCode as Hotkey string and overwrite evt.key.
    The modifiers are arranged in the same order as matplotlib as
    [LR]win + ctrl + alt(meta) + shift.
    """
    key = evt.GetKeyCode()
    mod = ""
    for k,v in ((wx.WXK_WINDOWS_LEFT, 'Lwin-'),
                (wx.WXK_WINDOWS_RIGHT, 'Rwin-'),
                (wx.WXK_CONTROL, 'C-'),
                (wx.WXK_ALT,     'M-'),
                (wx.WXK_SHIFT,   'S-')):
        if key != k and wx.GetKeyState(k):
            mod += v
    
    key = speckeys.get(key) or chr(key).lower()
    evt.key = mod + key
    return evt.key


def regulate_key(key):
    return (key.replace("ctrl+",  "C-") # modifier keys abbreviation
               .replace("alt+",   "M-")
               .replace("shift+", "S-")
               .replace("win+", "win-")
               .replace("M-C-", "C-M-") # modifier key regulation C-M-S-
               .replace("S-M-", "M-S-")
               .replace("S-C-", "C-S-"))


def postcall(f):
    """A decorator of wx.CallAfter
    Wx posts the message that forces `f to take place in the main thread.
    """
    @wraps(f)
    def _f(*args, **kwargs):
        wx.CallAfter(f, *args, **kwargs)
    return _f


def skip(v):
    v.Skip()


def noskip(v):
    pass


class CtrlInterface(object):
    """Mouse/Key event interface class
    """
    handler = property(lambda self: self.__handler)
    
    def __init__(self):
        self.__key = ''
        self.__handler = FSM({None:{}})
        
        ## self.Bind(wx.EVT_KEY_DOWN, self.on_hotkey_press)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_hotkey_press)
        self.Bind(wx.EVT_KEY_UP, self.on_hotkey_release)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)
        
        self.Bind(wx.EVT_LEFT_UP, lambda v: self._mouse_handler('Lbutton released', v))
        self.Bind(wx.EVT_RIGHT_UP, lambda v: self._mouse_handler('Rbutton released', v))
        self.Bind(wx.EVT_MIDDLE_UP, lambda v: self._mouse_handler('Mbutton released', v))
        self.Bind(wx.EVT_LEFT_DOWN, lambda v: self._mouse_handler('Lbutton pressed', v))
        self.Bind(wx.EVT_RIGHT_DOWN, lambda v: self._mouse_handler('Rbutton pressed', v))
        self.Bind(wx.EVT_MIDDLE_DOWN, lambda v: self._mouse_handler('Mbutton pressed', v))
        self.Bind(wx.EVT_LEFT_DCLICK, lambda v: self._mouse_handler('Lbutton dclick', v))
        self.Bind(wx.EVT_RIGHT_DCLICK, lambda v: self._mouse_handler('Rbutton dclick', v))
        self.Bind(wx.EVT_MIDDLE_DCLICK, lambda v: self._mouse_handler('Mbutton dclick', v))
        
        self.Bind(wx.EVT_MOUSE_AUX1_UP, lambda v: self._mouse_handler('Xbutton1 released', v))
        self.Bind(wx.EVT_MOUSE_AUX2_UP, lambda v: self._mouse_handler('Xbutton2 released', v))
        self.Bind(wx.EVT_MOUSE_AUX1_DOWN, lambda v: self._mouse_handler('Xbutton1 pressed', v))
        self.Bind(wx.EVT_MOUSE_AUX2_DOWN, lambda v: self._mouse_handler('Xbutton2 pressed', v))
        self.Bind(wx.EVT_MOUSE_AUX1_DCLICK, lambda v: self._mouse_handler('Xbutton1 dclick', v))
        self.Bind(wx.EVT_MOUSE_AUX2_DCLICK, lambda v: self._mouse_handler('Xbutton2 dclick', v))
        
        ## self.Bind(wx.EVT_MOTION, lambda v: self._window_handler('motion', v))
        self.Bind(wx.EVT_SET_FOCUS, lambda v: self._window_handler('focus_set', v))
        self.Bind(wx.EVT_KILL_FOCUS, lambda v: self._window_handler('focus_kill', v))
        self.Bind(wx.EVT_ENTER_WINDOW, lambda v: self._window_handler('window_enter', v))
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda v: self._window_handler('window_leave', v))
    
    def on_hotkey_press(self, evt): #<wx._core.KeyEvent>
        """Called when key down"""
        if evt.EventObject is not self:
            evt.Skip()
            return
        key = hotkey(evt)
        self.__key = regulate_key(key + '+')
        self.handler('{} pressed'.format(key), evt) or evt.Skip()
    
    def on_hotkey_release(self, evt): #<wx._core.KeyEvent>
        """Called when key up"""
        key = hotkey(evt)
        self.__key = ''
        self.handler('{} released'.format(key), evt) or evt.Skip()
    
    def on_mousewheel(self, evt): #<wx._core.MouseEvent>
        """Called when wheel event
        Trigger event: 'key+wheel[up|down|right|left] pressed'
        """
        if evt.GetWheelAxis():
            p = 'right' if evt.WheelRotation > 0 else 'left'
        else:
            p = 'up' if evt.WheelRotation > 0 else 'down'
        evt.key = self.__key + "wheel{}".format(p)
        self.handler('{} pressed'.format(evt.key), evt) or evt.Skip()
        self.__key = ''
    
    def _mouse_handler(self, event, evt): #<wx._core.MouseEvent>
        """Called when mouse event
        Trigger event: 'key+[LMRX]button pressed/released/dclick'
        """
        event = self.__key + event # 'C-M-S-K+[LMRX]button pressed/released/dclick'
        key, sep, st = event.rpartition(' ') # removes st:'pressed/released/dclick'
        evt.key = key or st
        self.handler(event, evt) or evt.Skip()
        self.__key = ''
        try:
            self.SetFocusIgnoringChildren() # let the panel accept keys
        except AttributeError:
            pass
    
    def _window_handler(self, event, evt): #<wx._core.FocusEvent> #<wx._core.MouseEvent>
        self.handler(event, evt) or evt.Skip()


class KeyCtrlInterfaceMixin(object):
    """Keymap interface mixin
    
    This interface class defines extended keymaps for inherited class handler.
    
    keymap : event key name that excluds 'pressed'
        global-map : 0 (default)
         ctl-x-map : 'C-x'
          spec-map : 'C-c'
           esc-map : 'escape'
    """
    def make_keymap(self, keymap, state=0, default=0):
        """Make a basis of extension map in the handler.
        """
        def _Pass(v):
            self.message("{} {}".format(keymap, v.key))
        _Pass.__name__ = str('pass')
        
        keyevent = keymap +' pressed'
        
        self.handler.update({ #<KeyCtrlInterfaceMixin.handler>
            state : {
                       keyevent : [ keymap, self.prefix_command_hook, skip ],
            },
            keymap : {
                         'quit' : [ default, ],
                    '* pressed' : [ default, _Pass ],
                 '*alt pressed' : [ keymap, _Pass ],
                '*ctrl pressed' : [ keymap, _Pass ],
               '*shift pressed' : [ keymap, _Pass ],
             '*[LR]win pressed' : [ keymap, _Pass ],
            },
        })
    
    def prefix_command_hook(self, evt):
        win = wx.Window.FindFocus()
        if isinstance(win, wx.TextEntry) and win.StringSelection\
        or isinstance(win, stc.StyledTextCtrl) and win.SelectedText:
          # or any other of pre-selection-p?
            self.handler('quit', evt)
            return
        self.message(evt.key + '-')
    
    def define_key(self, keymap, action=None, *args, **kwargs):
        """Define [map key] action at default state
        
        If no action, it invalidates the key and returns @decor(binder).
        key must be in C-M-S order (ctrl + alt(meta) + shift).
        
        kwargs: `doc` and `alias` are reserved as kw-only-args.
        """
        state = self.handler.default_state
        map, sep, key = regulate_key(keymap).rpartition(' ')
        map = map.strip()
        if not map:
            map = state
        elif map == '*':
            map = None
        elif map not in self.handler: # make key map automatically
            self.make_keymap(map)
        
        self.handler[map][key+' pressed'] = transaction = [state] # overwrite transaction
        self.handler.validate(map)
        if action:
            transaction.append(funcall(action, *args, **kwargs))
            return action
        return lambda f: self.define_key(keymap, f, *args, **kwargs)


## --------------------------------
## wx Framework and Designer
## --------------------------------

def ID_(id):
    ## Free ID - どこで使っているか検索できるように
    ## do not use [ID_LOWEST(4999):ID_HIGHEST(5999)]
    id += wx.ID_HIGHEST
    assert not wx.ID_LOWEST <= id <= wx.ID_HIGHEST
    return id


def pack(self, *args,
         orient=wx.HORIZONTAL,
         style=(0, wx.EXPAND | wx.ALL, 0),
         label=None):
    """Do layout

Usage:
    self.SetSizer(
        pack(self,
            (label, 0, wx.ALIGN_CENTER | wx.LEFT, 4),
            ( ctrl, 1, wx.ALIGN_CENTER | wx.LEFT, 4),
        )
    )
    *args : wx objects `obj (with some packing directives)
          - (obj, 1) -> sized with ratio 1 (orient と同方向)
                        他に 0 以外を指定しているオブジェクトとエリアを分け合う
          - (obj, 1, wx.EXPAND) -> expanded with ratio 1 (orient と垂直方向)
          - (obj, 0, wx.ALIGN_CENTER | wx.LEFT, 4) -> center with 4 pixel at wx.LEFT
          - ((-1,-1), 1, wx.EXPAND) -> stretched space
          - (-1,-1) -> padding space
          - None -> phantom
 **kwargs : 
   orient : HORIZONTAL or VERTICAL
    style : (proportion, flag, border)
            flag-expansion -> EXPAND, SHAPED
            flag-border -> TOP, BOTTOM, LEFT, RIGHT, ALL
            flag-align -> ALIGN_CENTER, ALIGN_LEFT, ALIGN_TOP, ALIGN_RIGHT, ALIGN_BOTTOM,
                          ALIGN_CENTER_VERTICAL, ALIGN_CENTER_HORIZONTAL
    label : label of StaticBox
    """
    if label is not None:
        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, orient)
    else:
        sizer = wx.BoxSizer(orient)
    
    for item in args:
        if not item:
            if item is None:
                item = (0,0), 0,0,0, # dummy spacing with null style
            else:
                item = (0,0) # padding with specified style
        try:
            try:
                sizer.Add(item, *style) # using style
            except TypeError:
                sizer.Add(*item) # using item-specific style
        except TypeError as e:
            traceback.print_exc()
            bmp = wx.ArtProvider.GetBitmap(wx.ART_ERROR, size=(16,16))
            err = wx.StaticBitmap(self, bitmap=bmp)
            err.SetToolTip("Pack failure\n{}".format(e))
            sizer.Add(err, *style)
            wx.Bell()
    return sizer


class Menu(wx.Menu):
    """Construct menu
    
    item: (id, text, hint, style, icon,  ... Menu.Append arguments
             action, updater, highlight) ... Menu Event handlers
        
        style -> menu style (ITEM_NORMAL, ITEM_CHECK, ITEM_RADIO)
         icon -> menu icon (bitmap)
       action -> EVT_MENU handler
      updater -> EVT_UPDATE_UI handler
    highlight -> EVT_MENU_HIGHLIGHT handler
    """
    def __init__(self, owner, values):
        wx.Menu.__init__(self)
        self.owner = owner
        
        for item in values:
            if not item:
                self.AppendSeparator()
                continue
            id = item[0]
            handlers = [x for x in item if callable(x)]
            icons =  [x for x in item if isinstance(x, wx.Bitmap)]
            argv = [x for x in item if x not in handlers and x not in icons]
            if isinstance(id, int):
                menu_item = wx.MenuItem(self, *argv) # <- menu_item.Id
                if icons:
                    menu_item.SetBitmaps(*icons)
                self.Append(menu_item)
                try:
                    self.owner.Bind(wx.EVT_MENU, handlers[0], id=id)
                    self.owner.Bind(wx.EVT_UPDATE_UI, handlers[1], id=id)
                    self.owner.Bind(wx.EVT_MENU_HIGHLIGHT, handlers[2], id=id)
                except IndexError:
                    pass
            else:
                subitems = argv.pop()
                submenu = Menu(owner, subitems)
                submenu_item = wx.MenuItem(self, wx.ID_ANY, *argv)
                submenu_item.SetSubMenu(submenu)
                if icons:
                    submenu_item.SetBitmaps(*icons)
                self.Append(submenu_item)
                self.Enable(submenu_item.Id, len(subitems)) # Disable an empty menu
                submenu.Id = submenu_item.Id # <- ID_ANY
    
    @staticmethod
    def Popup(parent, menu, *args, **kwargs):
        menu = Menu(parent, menu)
        parent.PopupMenu(menu, *args, **kwargs)
        menu.Destroy()


class MenuBar(wx.MenuBar, TreeList):
    """Construct menubar as is ordered menu:list
    リストの順番どおりに GUI 上にマップしたメニューバーを構築する
    
    root:TreeList is a nested list (as directory structrue)
    ├ [key, [item,
    │        item,...]],
    ：
    ├ [key, [item,
    │        item,
    │        submenu => [key, [item,
    ：        ...               item,...]],
    """
    def __init__(self, *args, **kwargs):
        wx.MenuBar.__init__(self, *args, **kwargs)
        TreeList.__init__(self)
    
    def getmenu(self, key, root=None):
        ## key = key.replace('\\', '/')
        if '/' in key:
            a, b = key.split('/', 1)
            branch = self.getmenu(a, root)
            return self.getmenu(b, branch)
        if root is None:
            return next((menu for menu, label in self.Menus if menu.Title == key), None)
        return next((item.SubMenu for item in root.MenuItems if item.ItemLabel == key), None)
    
    def update(self, key):
        """Update items of the menu that has specified key:root/branch
        Call when the menulist is changed.
        """
        if self.Parent:
            menu = self.getmenu(key)
            if not menu:     # 新規のメニューアイテムを挿入する
                self.reset() # リセットして終了
                return
            
            for item in menu.MenuItems: # delete all items
                self.Parent.Unbind(wx.EVT_MENU, id=item.Id)
                self.Parent.Unbind(wx.EVT_UPDATE_UI, id=item.Id)
                self.Parent.Unbind(wx.EVT_MENU_HIGHLIGHT, id=item.Id)
                menu.Delete(item)
            
            menu2 = Menu(self.Parent, self[key]) # new menu2 to swap menu
            for item in menu2.MenuItems:
                menu.Append(menu2.Remove(item)) # 重複しないようにいったん切り離して追加する
            
            if hasattr(menu, 'Id'):
                self.Enable(menu.Id, menu.MenuItemCount > 0) # 空のサブメニューは無効にする
    
    def reset(self):
        """Recreates menubar if the Parent were attached by SetMenuBar
        Call when the menulist is changed.
        """
        if self.Parent:
            for j in range(self.GetMenuCount()): # remove and del all top-level menu
                menu = self.Remove(0)
                for item in menu.MenuItems: # delete all items
                    self.Parent.Unbind(wx.EVT_MENU, id=item.Id)
                    self.Parent.Unbind(wx.EVT_UPDATE_UI, id=item.Id)
                    self.Parent.Unbind(wx.EVT_MENU_HIGHLIGHT, id=item.Id)
                menu.Destroy()
            
            for j, (key, values) in enumerate(self):
                menu = Menu(self.Parent, values) # 空のメインメニューでも表示に追加する
                self.Append(menu, key)
                if not values:
                    self.EnableTop(j, False) # 空のメインメニューは無効にする


class StatusBar(wx.StatusBar):
    """Construct statusbar with read/write
    
   field : list of field widths
    pane : index of status text field
    """
    lock = None
    
    def __init__(self, *args, **kwargs):
        wx.StatusBar.__init__(self, *args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        text = ' '.join(str(v) for v in args)
        if not self.lock:
            return self.write(text, **kwargs)
        return text
    
    def resize(self, field):
        self.SetFieldsCount(len(field))
        self.SetStatusWidths(list(field)) # oldver requires list type
    
    def write(self, text, pane=0):
        if text and text[0] == '\b':
            text = self.read(pane) + text[1:]
        self.SetStatusText(text, pane % self.GetFieldsCount())
        return text
    
    def read(self, pane=0):
        return self.GetStatusText(pane % self.GetFieldsCount())


class Frame(wx.Frame, KeyCtrlInterfaceMixin):
    """Frame base class
    
    menubar : MenuBar
  statusbar : StatusBar
 shellframe : mini-frame of the shell
    """
    handler = property(lambda self: self.__handler)
    message = property(lambda self: self.statusbar)
    
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        
        self.shellframe = ShellFrame(None, target=self)
        
        self.menubar = MenuBar()
        self.menubar["File"] = [
            (ID_(1), "&Shell\tF12", "Shell for inspection", wx.ITEM_CHECK,
                lambda v: (self.shellframe.Show(),
                           self.shellframe.console.CurrentPage.SetFocus()),
                lambda v: v.Check(self.shellframe.IsShown())),
            (),
            (wx.ID_EXIT, "E&xit\tCtrl-w", "Exit the program",
                lambda v: self.Close()),
                
            (wx.ID_ABOUT, "&About\tF1", "About this software",
                lambda v: self.About()),
        ]
        self.SetMenuBar(self.menubar)
        self.menubar.reset()
        
        self.statusbar = StatusBar(self)
        self.statusbar.resize((-1,78))
        self.SetStatusBar(self.statusbar)
        
        ## self.timer = wx.PyTimer(
        ##     lambda: self.statusbar.write(time.strftime('%m/%d %H:%M'), pane=-1))
        self.timer = wx.Timer(self)
        self.timer.Start(1000)
        
        def on_timer(evt):
            self.statusbar.write(time.strftime('%m/%d %H:%M'), pane=-1)
        self.Bind(wx.EVT_TIMER, on_timer)
        
        ## AcceleratorTable mimic
        def hook_char(evt):
            """Called when key down"""
            if isinstance(evt.EventObject, wx.TextEntry): # prior to handler
                evt.Skip()
            else:
                self.handler('{} pressed'.format(hotkey(evt)), evt) or evt.Skip()
        self.Bind(wx.EVT_CHAR_HOOK, hook_char)
        
        def close(v):
            """Close the window"""
            self.Close()
        
        self.__handler = FSM({ #<Frame.handler>
                0 : {
                    '* pressed' : (0, skip),
                  'M-q pressed' : (0, close),
                },
            },
            default = 0
        )
        self.make_keymap('C-x')
    
    def About(self):
        wx.MessageBox(__import__('__main__').__doc__ or 'no information',
                      "About this software")
    
    def Destroy(self):
        try:
            self.timer.Stop()
            self.shellframe.Destroy() # shellframe is not my child
        finally:
            return wx.Frame.Destroy(self)


class MiniFrame(wx.MiniFrame, KeyCtrlInterfaceMixin):
    """MiniFrame base class
    
    menubar : MenuBar (not created by default)
  statusbar : StatusBar (not shown by default)
    """
    handler = property(lambda self: self.__handler)
    message = property(lambda self: self.statusbar)
    
    def __init__(self, *args, **kwargs):
        wx.MiniFrame.__init__(self, *args, **kwargs)
        
        ## To disable, self.SetMenuBar(None)
        self.menubar = MenuBar()
        self.SetMenuBar(self.menubar)
        
        self.statusbar = StatusBar(self)
        self.statusbar.Show(0)
        self.SetStatusBar(self.statusbar)
        
        ## AcceleratorTable mimic
        def hook_char(evt):
            """Called when key down"""
            if isinstance(evt.EventObject, wx.TextEntry): # prior to handler
                evt.Skip()
            else:
                self.handler('{} pressed'.format(hotkey(evt)), evt) or evt.Skip()
        self.Bind(wx.EVT_CHAR_HOOK, hook_char)
        
        ## To default close >>> self.Unbind(wx.EVT_CLOSE)
        self.Bind(wx.EVT_CLOSE, lambda v: self.Show(0))
        
        def close(v):
            """Close the window"""
            self.Close()
        
        self.__handler = FSM({ #<MiniFrame.handler>
                0 : {
                    '* pressed' : (0, skip),
                  'M-q pressed' : (0, close),
                },
            },
            default = 0
        )
        self.make_keymap('C-x')
    
    def Destroy(self):
        return wx.MiniFrame.Destroy(self)


class ShellFrame(MiniFrame):
    """MiniFrame of shell for inspection, debug, and break `target

Attributes:
  rootshell : Nautilus root shell
    watcher : Notebook of global/locals info watcher
    console : Notebook of shells
      ghost : Notebook of editors and inspectors
    Scratch : temporary buffer for scratch (tooltip)
       Help : temporary buffer for help
        Log : logging buffer
    History : shell history (read only)
    monitor : wxmon.EventMonitor object
  inspector : wxwit.Inspector object

Args:
     target : Inspection target (any wx.Object)
              If the target is None, it will be __main__.
    """
    rootshell = property(lambda self: self.__shell)
    
    def __init__(self, parent, target=None, title=None, size=(1000,500),
                 style=wx.DEFAULT_FRAME_STYLE, **kwargs):
        MiniFrame.__init__(self, parent, size=size, style=style)
        
        if target is None:
            target = parent or __import__('__main__')
        
        self.Title = title or "Nautilus - {!r}".format(target)
        
        self.statusbar.resize((-1,120))
        self.statusbar.Show(1)
        
        self.Scratch = Editor(self)
        self.Help = Editor(self)
        self.Log = Editor(self)
        self.History = Editor(self)
        
        self.__shell = Nautilus(self, target,
            style=(wx.CLIP_CHILDREN | wx.BORDER_NONE), **kwargs)
        
        try:
            from wxpdb import Debugger
            from wxwit import Inspector
            from wxmon import EventMonitor
            from wxwil import LocalsWatcher
        except ImportError:
            from .wxpdb import Debugger
            from .wxwit import Inspector
            from .wxmon import EventMonitor
            from .wxwil import LocalsWatcher
        
        self.debugger = Debugger(self,
                                 stdin=self.__shell.interp.stdin,
                                 stdout=self.__shell.interp.stdout,
                                 skip=[Debugger.__module__,
                                       EventMonitor.__module__,
                                       FSM.__module__,
                                       'fnmatch', 'warnings', 'bdb', 'pdb',
                                       'wx.core', 'wx.lib.eventwatcher',
                                       ],
                                 )
        self.inspector = Inspector(self)
        self.monitor = EventMonitor(self)
        self.ginfo = LocalsWatcher(self)
        self.linfo = LocalsWatcher(self)
        
        self.console = aui.AuiNotebook(self, size=(600,400),
            style=(aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_BOTTOM)
                &~(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB | aui.AUI_NB_MIDDLE_CLICK_CLOSE)
        )
        self.console.AddPage(self.__shell, "root")
        self.console.TabCtrlHeight = 0
        
        self.console.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnConsolePageChanged)
        self.console.Bind(aui.EVT_AUINOTEBOOK_BUTTON, self.OnConsoleTabClose)
        
        self.ghost = aui.AuiNotebook(self, size=(600,400),
            style=(aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_BOTTOM)
                &~(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB | aui.AUI_NB_MIDDLE_CLICK_CLOSE)
        )
        self.ghost.AddPage(self.Scratch, "*Scratch*")
        self.ghost.AddPage(self.Help,    "*Help*")
        self.ghost.AddPage(self.Log,     "Log")
        self.ghost.AddPage(self.History, "History")
        self.ghost.AddPage(self.monitor, "Monitor")
        self.ghost.AddPage(self.inspector, "Inspector")
        self.ghost.TabCtrlHeight = -1
        
        self.watcher = aui.AuiNotebook(self, size=(300,200),
            style=(aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_BOTTOM)
                &~(aui.AUI_NB_CLOSE_ON_ACTIVE_TAB | aui.AUI_NB_MIDDLE_CLICK_CLOSE)
        )
        self.watcher.AddPage(self.ginfo, "globals")
        self.watcher.AddPage(self.linfo, "locals")
        
        self._mgr = aui.AuiManager()
        self._mgr.SetManagedWindow(self)
        self._mgr.SetDockSizeConstraint(0.45, 0.5) # (w, h)/N
        
        self._mgr.AddPane(self.console,
                          aui.AuiPaneInfo().Name("console").CenterPane().Show(1))
        
        self._mgr.AddPane(self.ghost,
                          aui.AuiPaneInfo().Name("ghost")
                             .Caption("Ghost in the Shell").Right().Show(0))
        
        self._mgr.AddPane(self.watcher,
                          aui.AuiPaneInfo().Name("wathcer")
                             .Caption("Locals watch").Float().Show(0))
        
        self._mgr.Update()
        
        self.Unbind(wx.EVT_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        
        self.findDlg = None
        self.findData = wx.FindReplaceData(wx.FR_DOWN | wx.FR_MATCHCASE)
        
        self.Bind(wx.EVT_FIND, self.OnFindNext)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFindNext)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
        
        def fork(v):
            """Fork key events to the debugger"""
            self.debugger.handler(self.handler.event, v)
        
        self.handler.update({ #<ShellFrame.handler>
            None : {
                  'debug_begin' : [ None, self.on_debug_begin ],
                   'debug_next' : [ None, self.on_debug_next ],
                    'debug_end' : [ None, self.on_debug_end ],
                'monitor_begin' : [ None, self.on_monitor_begin ],
                  'monitor_end' : [ None, self.on_monitor_end ],
                  'add_history' : [ None, self.add_history ],
                     'put_help' : [ None, self.put_help ],
                     'add_page' : [ None, self.add_page ],
                    'show_page' : [ None, self.show_page ],
                  'remove_page' : [ None, self.remove_page ],
                 'title_window' : [ None, self.SetTitleWindow ],
            },
            0 : {
                    '* pressed' : (0, skip, fork), # -> debugger
                   'f1 pressed' : (0, self.About),
                  'M-f pressed' : (0, self.OnFilterText),
                  'C-f pressed' : (0, self.OnFindText),
                   'f3 pressed' : (0, self.OnFindNext),
                 'S-f3 pressed' : (0, self.OnFindPrev),
                  'f11 pressed' : (0, _F(self.show_page, self.ghost, None, doc="Toggle ghost")),
                  'f12 pressed' : (0, _F(self.Close, alias="close", doc="Close the window")),
                'S-f12 pressed' : (0, _F(self.clear_shell)),
                'C-f12 pressed' : (0, _F(self.clone_shell)),
                'M-f12 pressed' : (0, _F(self.close_shell)),
                  'C-w pressed' : (0, _F(self.close_shell)),
                  'C-d pressed' : (0, _F(self.duplicate_line, clear=0)),
                'C-S-d pressed' : (0, _F(self.duplicate_line, clear=1)),
               'M-left pressed' : (0, _F(self.other_window, p=-1)),
              'M-right pressed' : (0, _F(self.other_window, p=+1)),
             'Xbutton1 pressed' : (0, _F(self.other_editor, p=-1)),
             'Xbutton2 pressed' : (0, _F(self.other_editor, p=+1)),
            },
            'C-x' : {
                    'l pressed' : (0, _F(self.show_page, self.Log, doc="Show Log")),
                    'h pressed' : (0, _F(self.show_page, self.Help, doc="Show Help")),
                  'S-h pressed' : (0, _F(self.show_page, self.History, doc="Show History")),
                    'j pressed' : (0, _F(self.show_page, self.Scratch, doc="Show Scratch")),
                    'm pressed' : (0, _F(self.show_page, self.monitor, doc="Show monitor")),
                    'i pressed' : (0, _F(self.show_page, self.inspector, doc="Show wit")),
                    'r pressed' : (0, _F(self.show_page, self.rootshell, doc="Show root shell")),
                 'home pressed' : (0, _F(self.show_page, self.rootshell, doc="Show root shell")),
                    'p pressed' : (0, _F(self.other_editor, p=-1)),
                    'n pressed' : (0, _F(self.other_editor, p=+1)),
            },
        })
        
        self.Scratch.set_style(Nautilus.PALETTE_STYLE)
        self.Scratch.show_folder()
        
        @self.Scratch.handler.bind('focus_set')
        def activate(v):
            self.SetTitleWindow(self.current_shell.target)
        
        @self.Scratch.handler.bind('f5 pressed')
        def eval(v):
            try:
                self.Scratch.linemark = None
                exec(self.Scratch.Text, self.current_shell.locals)
                dispatcher.send(signal='Interpreter.push',
                                sender=self, command=None, more=False)
            except Exception as e:
                ## traceback.print_exc()
                err = re.findall(r"File \".*\", line ([0-9]+)",
                                 traceback.format_exc(), re.I)
                if err:
                    self.Scratch.linemark = int(err[-1]) - 1
                self.message("- {!r}".format(e))
        
        self.Log.show_folder()
        
        @self.Log.handler.bind('line_set')
        def start(v):
            filename = self.Log.target
            if filename and not self.debugger.busy:
                self.debugger.watch((filename, v))
                self.Log.MarkerDeleteAll(4)
        
        @self.Log.handler.bind('line_unset')
        def stop(v):
            if not self.debugger.busy: # don't unset while debugging
                self.debugger.unwatch()
                self.Log.MarkerAdd(v, 4)
        
        self.Init()
        self._mgr.Update()
    
    SESSION_FILE = ut.get_rootpath("debrc")
    SCRATCH_FILE = ut.get_rootpath("deb-scratch.log")
    LOGGING_FILE = ut.get_rootpath("deb-logging.log")
    HISTORY_FILE = ut.get_rootpath("deb-history.log")
    
    @staticmethod
    def fopen(f, *args):
        return open(f, *args, newline='') # PY3
    
    def OnClose(self, evt):
        if self.debugger.busy:
            wx.MessageBox("The debugger is running\n\n"
                          "Enter [q]uit to exit before closing.")
            return
        self.Show(0) # Don't destroy the window
        self.debugger.unwatch()
    
    def OnDestroy(self, evt):
        nb = self.console
        if nb and nb.PageCount == 1:
            nb.TabCtrlHeight = 0
        evt.Skip()
    
    def Init(self):
        f = self.SCRATCH_FILE
        if os.path.isfile(f):
            with self.fopen(self.SCRATCH_FILE) as i:
                self.Scratch.Text = i.read()
                self.Scratch.EmptyUndoBuffer()
        
        f = self.LOGGING_FILE
        if os.path.isfile(f):
            with self.fopen(f) as i:
                self.Log.Text = i.read()
                self.Log.EmptyUndoBuffer()
        
        f = self.HISTORY_FILE
        if os.path.isfile(f):
            with self.fopen(f, 'a') as o:
                o.write("\r\n#! Edit: <{}>\r\n".format(datetime.datetime.now()))
        else:
            with self.fopen(f, 'w') as o: # as a new file
                pass
        
        try:
            ## load-session
            with open(self.SESSION_FILE) as i:
                exec(i.read())
        except FileNotFoundError:
            pass
        except Exception:
            traceback.print_exc()
            print("- Failed to load session")
    
    def Destroy(self):
        try:
            with self.fopen(self.SCRATCH_FILE, 'w') as o:
                o.write(self.Scratch.Text)
            
            with self.fopen(self.LOGGING_FILE, 'w') as o:
                o.write(self.Log.Text)
            
            with self.fopen(self.HISTORY_FILE, 'w') as o:
                o.write("#! Last updated: <{}>\r\n".format(datetime.datetime.now()))
                o.write(self.History.Text)
            
            ## save-session
            with open(self.SESSION_FILE, 'w') as o:
                o.write('\n'.join((
                    "#! Session file (This file is generated automatically)",
                    "self.SetSize({})".format(self.Size),
                    "self.Log.load({!r}, {})".format(self.Log.target,
                                                     self.Log.MarkerNext(0,1)+1),
                    "self.Log.EmptyUndoBuffer()",
                    "self.ghost.SetSelection({})".format(self.ghost.Selection),
                    "self.watcher.SetSelection({})".format(self.watcher.Selection),
                    "self._mgr.LoadPerspective({!r})".format(self._mgr.SavePerspective()),
                    ""
                )))
        except Exception:
            traceback.print_exc()
            print("- Failed to save session")
        finally:
            self._mgr.UnInit()
            return MiniFrame.Destroy(self)
    
    def About(self, evt=None):
        self.Help.SetText('\n\n'.join((
            "#<module 'mwx' from {!r}>".format(__file__),
            "Author: {!r}".format(__author__),
            "Version: {!s}".format(__version__),
            self.__shell.__doc__,
            
            "================================\n" # Thanks to wx.py.shell
            "#{!r}".format(wx.py.shell),
            "Author: {!r}".format(wx.py.version.__author__),
            "Version: {!s}".format(wx.py.version.VERSION),
            wx.py.__doc__,
            wx.py.shell.__doc__,
            "*original{}".format(wx.py.shell.HELP_TEXT.lower().replace('\n', '\n\t')),
            
            "================================\n" # Thanks are also due to Phoenix/wxWidgets
            "#{!r}".format(wx),
            "To show the credit, press C-M-Mbutton.",
            ))
        )
        self.show_page(self.Help, focus=0)
    
    def PopupWindow(self, win, show=True):
        """Popup window in notebooks (console, ghost)
        win : page or window to popup (default:None is ghost)
       show : True, False, otherwise None:toggle
        """
        for pane in self._mgr.GetAllPanes():
            nb = pane.window
            if nb is win:
                break
            if isinstance(nb, aui.AuiNotebook):
                j = nb.GetPageIndex(win)
                if j != -1:
                    if j != nb.Selection:
                        nb.Selection = j # move focus to AuiTab?
                    break
        else:
            print("- No such window in any pane: {}.".format(win))
            return
        pane = self._mgr.GetPane(nb)
        if show is None:
            show = not pane.IsShown()
        pane.Show(show)
        self._mgr.Update()
    
    def SetTitleWindow(self, title):
        self.Title = "Nautilus - {}".format(title)
    
    def OnConsolePageChanged(self, evt): #<wx._aui.AuiNotebookEvent>
        nb = self.console
        if nb.CurrentPage is self.__shell:
            nb.WindowStyle &= ~wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        else:
            nb.WindowStyle |= wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        evt.Skip()
    
    def OnConsoleTabClose(self, evt): #<wx._aui.AuiNotebookEvent>
        tab = evt.EventObject                 #<wx._aui.AuiTabCtrl>
        win = tab.Pages[evt.Selection].window # Don't use GetPage for split notebook
        if win is self.__shell:
            self.message("- Don't remove the root shell.")
        else:
            evt.Skip()
    
    ## --------------------------------
    ## Actions for handler
    ## --------------------------------
    
    def debug(self, obj, *args, **kwargs):
        if isinstance(obj, wx.Object) or obj is None:
            self.inspector.watch(obj)
            self.monitor.watch(obj)
            self.linfo.watch(obj.__dict__)
            self.ginfo.watch(eval("globals()", obj.__dict__))
            self.console.SetFocus() # focus orginal-window
            self.show_page(self.linfo, focus=0)
            self.show_page(self.monitor, focus=0)
        elif callable(obj):
            def _trace():
                self.__shell.clearCommand()
                self.debugger.debug(obj, *args, **kwargs)
            wx.CallAfter(_trace)
        else:
            print("- cannot debug {!r}".format(obj))
            print("  the target must be callable or wx.Object.")
        return obj
    
    def on_debug_begin(self, frame):
        """Called before set_trace"""
        self.add_history(self.__shell.cmdline)
        self.__shell.write("#<< Enter [n]ext to continue.\n", -1)
        self.__shell.SetFocus()
        self.Show()
        self.Log.clear()
        self.show_page(self.Log, focus=0)
        self.show_page(self.linfo, focus=0)
    
    def on_debug_next(self, frame):
        """Called from cmdloop"""
        self.add_history(self.__shell.cmdline)
        self.__shell.globals = self.debugger.globals
        self.__shell.locals = self.debugger.locals
        self.ginfo.watch(self.debugger.globals)
        self.linfo.watch(self.debugger.locals)
        self.show_page(self.Log, focus=0)
        self.SetTitleWindow(frame)
        self.Log.target = frame.f_code.co_filename
        dispatcher.send(signal='Interpreter.push',
                        sender=self, command=None, more=False)
    
    def on_debug_end(self, frame):
        """Called after set_quit"""
        self.add_history(self.__shell.cmdline)
        self.__shell.write("#>> Debugger closed successfully.", -1)
        self.__shell.prompt()
        self.linfo.unwatch()
        self.ginfo.unwatch()
        del self.__shell.locals
        del self.__shell.globals
    
    def on_monitor_begin(self, widget):
        """Called when monitor watch"""
        self.inspector.set_colour(widget, 'blue')
        obj = widget.__class__
        filename = inspect.getsourcefile(obj)
        if filename:
            src, lineno = inspect.getsourcelines(obj)
            self.Log.load(filename, lineno)
        self.Log.target = filename
    
    def on_monitor_end(self, widget):
        """Called when monitor unwatch"""
        self.inspector.set_colour(widget, 'black')
        self.Log.target = None
    
    def show_page(self, win, show=True, focus=True):
        """Show the notebook page and move the focus
        win : page or window to popup (default:None is ghost)
       show : True, False, otherwise None:toggle
        """
        wnd = win if focus else wx.Window.FindFocus() # original focus
        self.PopupWindow(win, show)
        if wnd and win.Shown:
            wnd.SetFocus()
    
    def add_page(self, win, title=None, show=True):
        """Add page to the console"""
        nb = self.console
        j = nb.GetPageIndex(win)
        if j == -1:
            nb.AddPage(win, title or typename(win))
            nb.TabCtrlHeight = -1
        self.PopupWindow(win, show)
    
    def remove_page(self, win):
        """Remove page from the console"""
        nb = self.console
        j = nb.GetPageIndex(win)
        if j != -1:
            nb.RemovePage(j)
            if nb.PageCount == 1:
                nb.TabCtrlHeight = 0
        win.Show(0)
    
    def put_help(self, text, show=True, focus=False):
        """Puts text to the help buffer"""
        self.Help.Text = text
        if show is not None:
            self.show_page(self.Help, show, focus)
    
    def add_history(self, command, noerr=None):
        """Add command:text to the history buffer"""
        if command.isspace():
            return
        
        ed = self.History
        ed.ReadOnly = 0
        ed.write(command)
        ln = ed.LineFromPosition(ed.TextLength - len(command))
        if noerr is not None:
            if noerr:
                ed.MarkerAdd(ln, 1) # white-marker
            else:
                ed.MarkerAdd(ln, 2) # error-marker
        ed.ReadOnly = 1
        
        f = self.HISTORY_FILE
        if os.path.isfile(f):
            with self.fopen(f, 'a') as o:
                o.write(command)
    
    def other_editor(self, p=1):
        "Focus moves to other page (no loop)"
        win = wx.Window.FindFocus()
        nb = win.Parent
        if nb in (self.console, self.ghost):
            nb.Selection += p
    
    def other_window(self, p=1):
        "Focus moves to other window"
        win = wx.Window.FindFocus()
        pages = [win for win in self.all_pages()
                 if isinstance(win, EditorInterface) and win.IsShownOnScreen()]
        if win in pages:
            j = (pages.index(self.current_editor) + p) % len(pages)
            pages[j].SetFocus()
    
    def duplicate_line(self, clear=True):
        """Duplicate an expression at the caret-line"""
        win = self.current_editor
        text = win.SelectedText or win.expr_at_caret
        if text:
            shell = self.current_shell
            if clear:
                shell.clearCommand()
            shell.write(text, -1)
            shell.SetFocus()
    
    def clear_shell(self):
        """Clear the current shell"""
        shell = self.current_shell
        shell.clear()
        self.handler('shell_cleared', shell)
    
    def clone_shell(self, target=None):
        """Clone the current shell"""
        shell = self.current_shell
        shell.clone(target or shell.target)
        self.handler('shell_cloned', shell)
    
    def close_shell(self):
        """Close the current shell"""
        shell = self.current_shell
        if shell is self.__shell:
            self.message("- Don't remove the root shell.")
            return
        nb = self.console
        j = nb.GetPageIndex(shell)
        if j != -1:
            nb.DeletePage(j)
            self.handler('shell_closed', None)
    
    ## --------------------------------
    ## Find text dialog
    ## --------------------------------
    
    def all_pages(self):
        for nb in (self.console, self.ghost):
            for j in range(nb.PageCount):
                yield nb.GetPage(j)
    
    @property
    def current_editor(self):
        win = wx.Window.FindFocus()
        if win in self.all_pages():
            if isinstance(win, EditorInterface):
                return win
        return self.console.CurrentPage
    
    @property
    def current_shell(self):
        return self.console.CurrentPage
    
    def OnFilterText(self, evt):
        win = self.current_editor
        text = win.topic_at_caret
        if not text:
            self.message("- No word to filter")
            for i in range(2):
                win.SetIndicatorCurrent(i)
                win.IndicatorClearRange(0, win.TextLength)
            return
        word = text.encode() # for multi-byte string
        raw = win.TextRaw
        lw = len(word)
        pos = -1
        n = 0
        while 1:
            pos = raw.find(word, pos+1)
            if pos < 0:
                break
            for i in range(2):
                win.SetIndicatorCurrent(i)
                win.IndicatorFillRange(pos, lw)
            n += 1
        self.message("{}: {} found".format(text, n))
        self.findData.FindString = text
    
    ## *** The following code is a modification of <wx.py.frame.Frame> ***
    
    def OnFindText(self, evt):
        if self.findDlg is not None:
            self.findDlg.SetFocus()
            return
        
        win = self.current_editor
        self.findData.FindString = win.topic_at_caret
        self.findDlg = wx.FindReplaceDialog(win, self.findData, "Find",
                            style=(wx.FR_NOWHOLEWORD | wx.FR_NOUPDOWN))
        self.findDlg.Show()
    
    def OnFindNext(self, evt, backward=False): #<wx._core.FindDialogEvent>
        if self.findDlg:
            self.findDlg.Close()
            self.findDlg = None
        
        data = self.findData
        down_p = data.Flags & wx.FR_DOWN
        if (backward and down_p) or (not backward and not down_p):
            data.Flags ^= wx.FR_DOWN # toggle up/down flag
        
        win = self.current_editor # or self.findDlg.Parent <EditWindow>
        win.DoFindNext(data)
    
    def OnFindPrev(self, evt):
        self.OnFindNext(evt, backward=True)
    
    def OnFindClose(self, evt): #<wx._core.FindDialogEvent>
        self.findDlg.Destroy()
        self.findDlg = None


def editable(f):
    @wraps(f)
    def _f(self, *args, **kwargs):
        if self.CanEdit():
            return f(self, *args, **kwargs)
    return _f


class EditorInterface(CtrlInterface, KeyCtrlInterfaceMixin):
    """Python code editor interface with Keymap
    
    Note: This class should be mixed-in `wx.stc.StyledTextCtrl`
    """
    message = print
    
    def __init__(self):
        CtrlInterface.__init__(self)
        
        self.make_keymap('C-x')
        self.make_keymap('C-c')
        
        self.handler.update({ #<Editor.handler>
            -1 : {  # original action of the Editor
                    '* pressed' : (0, skip, lambda v: self.message("ESC {}".format(v.key))),
                 '*alt pressed' : (-1, ),
                '*ctrl pressed' : (-1, ),
               '*shift pressed' : (-1, ),
             '*[LR]win pressed' : (-1, ),
            },
            0 : {
                    '* pressed' : (0, skip),
                   '* released' : (0, skip),
               'escape pressed' : (-1, _F(lambda v: self.message("ESC-"), alias="escape")),
               'insert pressed' : (0, _F(self.over, None, doc="toggle-over")),
                   'f9 pressed' : (0, _F(self.wrap, None, doc="toggle-fold-type")),
               'C-left pressed' : (0, _F(self.WordLeft)),
              'C-right pressed' : (0, _F(self.WordRightEnd)),
             'C-S-left pressed' : (0, _F(self.selection_backward_word_or_paren)),
            'C-S-right pressed' : (0, _F(self.selection_forward_word_or_paren)),
               'C-S-up pressed' : (0, _F(self.LineUpExtend)),
             'C-S-down pressed' : (0, _F(self.LineDownExtend)),
                  'C-a pressed' : (0, _F(self.beggining_of_line)),
                  'C-e pressed' : (0, _F(self.end_of_line)),
                  'M-a pressed' : (0, _F(self.back_to_indentation)),
                  'M-e pressed' : (0, _F(self.end_of_line)),
                  'C-k pressed' : (0, _F(self.kill_line)),
                  'C-l pressed' : (0, _F(self.recenter)),
                'C-S-l pressed' : (0, _F(self.recenter)), # override delete-line
                  'C-t pressed' : (0, noskip), # override transpose-line
                'C-S-f pressed' : (0, _F(self.set_marker)), # override mark
              'C-space pressed' : (0, _F(self.set_marker)),
              'S-space pressed' : (0, _F(self.set_line_marker)),
                  'C-@ pressed' : (0, _F(self.goto_marker)),
                'C-S-@ pressed' : (0, _F(self.goto_line_marker)),
          'C-backspace pressed' : (0, skip),
          'S-backspace pressed' : (0, _F(self.backward_kill_line)),
                'C-tab pressed' : (0, _F(self.insert_space_like_tab)),
              'C-S-tab pressed' : (0, _F(self.delete_backward_space_like_tab)),
                  'tab pressed' : (0, _F(self.indent_line)),
                'S-tab pressed' : (0, skip),
                  ## 'C-/ pressed' : (0, ), # cf. C-a home
                  ## 'C-\ pressed' : (0, ), # cf. C-e end
            },
            'C-x' : {
                    '* pressed' : (0, skip),
                    '[ pressed' : (0, skip, _F(self.goto_char, pos=0, doc="beginning-of-buffer")),
                    '] pressed' : (0, skip, _F(self.goto_char, pos=-1, doc="end-of-buffer")),
            },
            'C-c' : {
                    '* pressed' : (0, skip),
                  'C-c pressed' : (0, _F(self.goto_matched_paren)),
            },
        })
        self.handler.clear(0)
        
        ## cf. wx.py.editwindow.EditWindow.OnUpdateUI => Check for brace matching
        self.Bind(stc.EVT_STC_UPDATEUI,
                  lambda v: self.match_paren()) # no skip
        
        ## Keyword(2) setting
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, ' '.join(keyword.kwlist))
        self.SetKeyWords(1, ' '.join(builtins.__dict__) + ' self this')
        
        ## Global style for all languages
        ## wx.Font style
        ##    family : DEFAULT, DECORATIVE, ROMAN, SCRIPT, SWISS, MODERN, TELETYPE
        ##     slant : NORMAL, SLANT, ITALIC
        ##    weight : NORMAL, LIGHT, BOLD
        ## underline : False
        ## font = wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL, False, "MS Gothic")
        ## self.StyleSetFont(stc.STC_STYLE_DEFAULT, font)
        
        ## self.StyleClearAll()
        ## self.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
        ## self.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        
        ## The magin style for line numbers and symbols
        ## [0] for markers, 10 pixels wide, mask 0b11111
        ## [1] for numbers, 32 pixels wide, mask 0x01ffffff (~stc.STC_MASK_FOLDERS)
        ## [2] for borders,  1 pixels wide, mask 0xfe000000 ( stc.STC_MASK_FOLDERS)
        
        ## 32 bit margin mask
        ## [0] 1111,1111,1111,1111,1111,1111,1111,1111 = -1 for all markers
        ## [1] 0000,0001,1111,1111,1111,1111,1111,1111 = 0x01ffffff for markers
        ## [2] 1111,1110,0000,0000,0000,0000,0000,0000 = 0xfe000000 for folders
        
        self.SetMarginType(0, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(0, 0b00111) # mask for markers (0,1,2)
        self.SetMarginWidth(0, 10)
        
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginMask(1, 0b11000) # mask for pointer (3,4)
        self.SetMarginWidth(1, 32)
        
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS) # mask for folders
        self.SetMarginWidth(2, 1)
        self.SetMarginSensitive(2, False)
        
        ## if wx.VERSION >= (4,1,0):
        try:
            self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
            self.Bind(stc.EVT_STC_MARGIN_RIGHT_CLICK, self.OnMarginRClick)
        except AttributeError:
            pass
        
        self.SetProperty('fold', '1') # Enable folder at margin=2
        self.SetMarginLeft(2) # +1 margin at the left
        
        ## Custom markers (cf. MarkerAdd)
        self.MarkerDefine(0, stc.STC_MARK_CIRCLE, '#007ff0', "#007ff0") # o blue-mark
        self.MarkerDefine(1, stc.STC_MARK_ARROW,  '#000000', "#ffffff") # > white-arrow
        self.MarkerDefine(2, stc.STC_MARK_ARROW,  '#7f0000', "#ff0000") # > red-arrow
        self.MarkerDefine(3, stc.STC_MARK_SHORTARROW, 'blue', "gray")   # >> pointer
        self.MarkerDefine(4, stc.STC_MARK_SHORTARROW, 'red', "yellow")  # >> red-pointer
        
        v = ('white', 'black')
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS, *v)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,  *v)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,    *v)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,  *v)
        ## self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_TCORNER, *v)
        ## self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_TCORNER, *v)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_VLINE, *v)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_VLINE, *v)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_VLINE, *v)
        
        ## Custom indicator for search-word
        try:
            self.IndicatorSetStyle(0, stc.STC_INDIC_TEXTFORE)
            self.IndicatorSetStyle(1, stc.STC_INDIC_ROUNDBOX)
        except AttributeError:
            self.IndicatorSetStyle(0, stc.STC_INDIC_PLAIN)
            self.IndicatorSetStyle(1, stc.STC_INDIC_ROUNDBOX)
        self.IndicatorSetForeground(0, "red")
        self.IndicatorSetForeground(1, "yellow")
        
        ## Custom indicator for match_paren
        self.IndicatorSetStyle(2, stc.STC_INDIC_PLAIN)
        self.IndicatorSetForeground(2, "light gray")
        
        ## Custom style of control-char, wrap-mode
        ## self.ViewEOL = True
        ## self.ViewWhiteSpace = True
        ## self.TabWidth = 4
        ## self.UseTabs = False
        self.WrapMode = 0
        self.WrapIndentMode = 1
        self.IndentationGuides = 1
        
        self.__mark = None
        self.__line = None
    
    ## custom constants embedded in stc
    stc.STC_P_WORD3 = 20
    
    @property
    def mark(self):
        return self.__mark
    
    @mark.setter
    def mark(self, v):
        if v is None:
            del self.mark
            return
        self.__mark = v
        self.MarkerDeleteAll(0)
        ln = self.LineFromPosition(v)
        self.MarkerAdd(ln, 0)
        self.handler('mark_set', v)
    
    @mark.deleter
    def mark(self):
        v = self.__mark
        if v is None:
            return
        self.__mark = None
        self.MarkerDeleteAll(0)
        self.handler('mark_unset', v)
    
    def set_marker(self):
        self.mark = self.curpos
    
    def goto_marker(self):
        if self.mark is not None:
            self.goto_char(self.mark)
            self.recenter()
    
    @property
    def linemark(self):
        return self.__line
    
    @linemark.setter
    def linemark(self, ln):
        if ln is None:
            del self.linemark
            return
        self.__line = ln
        self.MarkerDeleteAll(3)
        self.MarkerAdd(ln, 3)
        self.handler('line_set', ln)
    
    @linemark.deleter
    def linemark(self):
        ln = self.__line
        if ln is None:
            return
        self.__line = None
        self.MarkerDeleteAll(3)
        self.handler('line_unset', ln)
    
    def set_line_marker(self):
        if self.linemark == self.curline:
            self.linemark = None # toggle
        else:
            self.linemark = self.curline
    
    def goto_line_marker(self):
        if self.linemark is not None:
            self.goto_line(self.linemark)
            self.recenter()
    
    ## --------------------------------
    ## Python syntax
    ## --------------------------------
    
    def indent_line(self):
        """Auto-indent the current line"""
        line = self.GetTextRange(self.bol, self.eol) # no-prompt
        lstr = line.strip()
        indent = self.calc_indent()
        if lstr in ('else:', 'elif:', 'except:', 'finally:'):
            indent = indent[:-4]
        pos = max(self.bol,
                  self.curpos - len(line) + len(lstr))
        self.Replace(self.bol, self.eol, indent + lstr)
        self.goto_char(pos + len(indent))
    
    def calc_indent(self):
        """Calculate indent spaces from prefious line
        (patch) `with` in wx.py.shell.Shell.prompt
        """
        line = self.GetLine(self.curline - 1)
        for p in (sys.ps1, sys.ps2, sys.ps3):
            if line.startswith(p):
                line = line[len(p):]
                break
        lstr = line.lstrip()
        if not lstr:
            indent = line.strip('\r\n') # remove line-seps: '\r' and '\n'
        else:
            indent = line[:(len(line)-len(lstr))]
            if line.strip()[-1] == ':':
                m = re.match(r"[a-z]+", lstr)
                if m and m.group(0) in (
                    'if','else','elif','for','while','with',
                    'def','class','try','except','finally'):
                    indent += ' '*4
        return indent
    
    ## --------------------------------
    ## Fold / Unfold functions
    ## --------------------------------
    
    def show_folder(self, show=True):
        ## Call this method *before* set_style
        if show:
            self.SetMarginWidth(2, 12)
            self.SetMarginSensitive(2, True)
            self.SetFoldMarginColour(True, self.CaretLineBackground)
            self.SetFoldMarginHiColour(True, 'light gray')
        else:
            self.SetMarginWidth(2, 1)
            self.SetMarginSensitive(2, False)
            self.SetFoldMarginColour(True, 'black')
            self.SetFoldMarginHiColour(True, 'black')
    
    def OnMarginClick(self, evt):
        lc = self.LineFromPosition(evt.Position)
        level = self.GetFoldLevel(lc) ^ stc.STC_FOLDLEVELBASE # header-flag or indent-level
        
        ## if level == stc.STC_FOLDLEVELHEADERFLAG: # fold the top-level header only
        if level: # fold any if the indent level is non-zero
            self.toggle_fold(lc)
    
    def OnMarginRClick(self, evt):
        lc = self.LineFromPosition(evt.Position)
        level = self.GetFoldLevel(lc) ^ stc.STC_FOLDLEVELBASE
        
        Menu.Popup(self, [
            (1, "&Fold ALL", wx.ArtProvider.GetBitmap(wx.ART_MINUS, size=(16,16)),
                lambda v: self.fold_all()),
                
            (2, "&Expand ALL", wx.ArtProvider.GetBitmap(wx.ART_PLUS, size=(16,16)),
                lambda v: self.unfold_all()),
        ])
    
    def toggle_fold(self, lc=None):
        """Toggle fold/unfold the header including the given line"""
        if lc is None:
            lc = self.curline
        while 1:
            lp = self.GetFoldParent(lc)
            if lp == -1:
                break
            lc = lp
        self.ToggleFold(lc)
    
    def fold_all(self):
        """Fold all headers"""
        ln = self.LineCount
        lc = 0
        while lc < ln:
            level = self.GetFoldLevel(lc) ^ stc.STC_FOLDLEVELBASE
            if level == stc.STC_FOLDLEVELHEADERFLAG:
                self.SetFoldExpanded(lc, False)
                le = self.GetLastChild(lc, -1)
                if le > lc:
                    self.HideLines(lc+1, le)
                lc = le
            lc = lc + 1
    
    def unfold_all(self):
        """Unfold all toplevel headers"""
        ln = self.LineCount
        lc = 0
        while lc < ln:
            level = self.GetFoldLevel(lc) ^ stc.STC_FOLDLEVELBASE
            if level == stc.STC_FOLDLEVELHEADERFLAG:
                self.SetFoldExpanded(lc, True)
                le = self.GetLastChild(lc, -1)
                if le > lc:
                    self.ShowLines(lc+1, le)
                lc = le
            lc = lc + 1
    
    ## --------------------------------
    ## Preferences / Appearance
    ## --------------------------------
    
    def set_style(self, spec=None, **kwargs):
        spec = spec and spec.copy() or {}
        spec.update(kwargs)
        
        def _map(sc):
            return dict(kv.partition(':')[::2] for kv in sc.split(','))
        
        if "STC_STYLE_DEFAULT" in spec:
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, spec.pop("STC_STYLE_DEFAULT"))
            self.StyleClearAll()
        
        if "STC_STYLE_LINENUMBER" in spec:
            lsc = _map(spec.get("STC_STYLE_LINENUMBER"))
            
            ## Set colors used as a chequeboard pattern,
            ## lo (back) one of the colors
            ## hi (fore) the other color
            if self.GetMarginSensitive(2):
                ## 12 pixel chequeboard, fore being default colour
                self.SetFoldMarginColour(True, lsc.get('back'))
                self.SetFoldMarginHiColour(True, 'light gray')
            else:
                ## one pixel solid line, the same colour as the line-number
                self.SetFoldMarginColour(True, lsc.get('fore'))
                self.SetFoldMarginHiColour(True, lsc.get('fore'))
        
        ## Custom style for caret and line colour
        if "STC_STYLE_CARETLINE" in spec:
            lsc = _map(spec.pop("STC_STYLE_CARETLINE"))
            
            self.SetCaretLineVisible(0)
            if 'fore' in lsc:
                self.SetCaretForeground(lsc['fore'])
            if 'back' in lsc:
                self.SetCaretLineBackground(lsc['back'])
                self.SetCaretLineVisible(1)
            if 'size' in lsc:
                self.SetCaretWidth(int(lsc['size']))
                self.SetCaretStyle(stc.STC_CARETSTYLE_LINE)
            if 'bold' in lsc:
                self.SetCaretStyle(stc.STC_CARETSTYLE_BLOCK)
        
        ## Custom indicator for search-word
        if "STC_P_WORD3" in spec:
            lsc = _map(spec.get("STC_P_WORD3"))
            
            self.IndicatorSetForeground(0, lsc.get('fore') or "red")
            self.IndicatorSetForeground(1, lsc.get('back') or "red")
        
        for key, value in spec.items():
            self.StyleSetSpec(getattr(stc, key), value)
    
    def match_paren(self):
        c = self.curpos
        if self.following_char in "({[<":
            pos = self.BraceMatch(c)
            if pos != -1:
                self.BraceHighlight(c, pos) # matched to following char
                return pos
            else:
                self.BraceBadLight(c)
        elif self.preceding_char in ")}]>":
            pos = self.BraceMatch(c-1)
            if pos != -1:
                self.BraceHighlight(pos, c-1) # matched to preceding char
                return pos
            else:
                self.BraceBadLight(c-1)
        else:
            self.BraceHighlight(-1,-1) # no highlight
    
    def over(self, mode=1):
        """Set insert or overtype
        mode in {0:insert, 1:over, None:toggle}
        """
        self.Overtype = mode if mode is not None else not self.Overtype
        self.Refresh()
    
    def wrap(self, mode=1):
        """Set fold type (override) of wrap
        mode in {0:no-wrap, 1:word-wrap, 2:char-wrap, None:toggle}
        """
        self.WrapMode = mode if mode is not None else not self.WrapMode
    
    def recenter(self, ln=None):
        """Scroll the cursor line to the center of screen
        If ln=0, the cursor moves to the top of the screen.
        If ln=-1, moves to the bottom
        """
        n = self.LinesOnScreen() # lines completely visible
        m = n//2 if ln is None else ln % n if ln < n else n
        w, h = self.PointFromPosition(self.curpos)
        L = h // self.TextHeight(0)
        ## self.ScrollLines(L - m) # a little delay?
        self.ScrollToLine(self.FirstVisibleLine + L - m)
    
    ## --------------------------------
    ## Attributes of the editor
    ## --------------------------------
    following_char = property(lambda self: chr(self.GetCharAt(self.curpos)))
    preceding_char = property(lambda self: chr(self.GetCharAt(self.curpos-1)))
    
    @property
    def following_symbol(self):
        """Similar to following_char, but skips whites"""
        ln = self.GetTextRange(self.curpos, self.eol)
        return next((c for c in ln if not c.isspace()), '')
    
    @property
    def preceding_symbol(self):
        """Similar to preceding_char, but skips whites"""
        ln = self.GetTextRange(self.bol, self.curpos)[::-1]
        return next((c for c in ln if not c.isspace()), '')
    
    curpos = property(
        lambda self: self.GetCurrentPos(),
        lambda self,v: self.SetCurrentPos(v))
    
    anchor = property(
        lambda self: self.GetAnchor(),
        lambda self,v: self.SetAnchor(v))
    
    ## CurrentLine (0-base number)
    curline = property(
        lambda self: self.GetCurrentLine(),
        lambda self,v: self.SetCurrentLine(v))
    
    @property
    def bol(self):
        """beginning of line"""
        text, lp = self.CurLine
        return self.curpos - lp
    
    @property
    def eol(self):
        """end of line"""
        text, lp = self.CurLine
        text = text.strip('\r\n') # remove line-seps: '\r' and '\n'
        return (self.curpos - lp + len(text.encode()))
    
    @property
    def expr_at_caret(self):
        """Pythonic expression at the caret
        The caret scouts back and forth to scoop a chunk of expression.
        """
        text, lp = self.CurLine
        ls, rs = text[:lp], text[lp:]
        lhs = ut._get_words_backward(ls) # or ls.rpartition(' ')[-1]
        rhs = ut._get_words_forward(rs) # or rs.partition(' ')[0]
        return (lhs + rhs).strip()
    
    @property
    def topic_at_caret(self):
        """Topic word at the caret or selected substring
        The caret scouts back and forth to scoop a topic.
        """
        return self.get_selection_or_topic()
    
    @property
    def right_paren(self):
        if self.following_char in "({[<":
            return self.BraceMatch(self.curpos) # (0 <= cur < pos+1)
        return -1
    
    @property
    def left_paren(self):
        if self.preceding_char in ")}]>":
            return self.BraceMatch(self.curpos-1) # (0 <= pos < cur-1)
        return -1
    
    @property
    def right_quotation(self):
        c = self.curpos
        text = self.GetTextRange(c, self.TextLength)
        if text and text[0] in "\"\'":
            try:
                lexer = shlex.shlex(text)
                return c + len(lexer.get_token())
            except ValueError:
                pass # no closing quotation
        return -1
    
    @property
    def left_quotation(self):
        c = self.curpos
        text = self.GetTextRange(0, c)[::-1]
        if text and text[0] in "\"\'":
            try:
                lexer = shlex.shlex(text)
                return c - len(lexer.get_token())
            except ValueError:
                pass # no closing quotation
        return -1
    
    ## --------------------------------
    ## Goto, Skip, Selection, etc.
    ## --------------------------------
    
    def goto_char(self, pos):
        if pos < 0:
            pos += self.TextLength + 1 # end-of-buffer (+1:\0)
        self.GotoPos(pos)
        return self.curpos
    
    def goto_line(self, ln):
        if ln < 0:
            ln += self.LineCount
        self.GotoLine(ln)
        return self.curpos
    
    def skip_chars_forward(self, rexpr=r'\s'):
        p = re.compile(rexpr)
        while p.search(self.following_char):
            c = self.curpos
            if c == self.TextLength:
                break
            self.GotoPos(c + 1)
        return self.curpos
    
    def skip_chars_backward(self, rexpr=r'\s'):
        p = re.compile(rexpr)
        while p.search(self.preceding_char):
            c = self.curpos
            if c == 0:
                break
            self.GotoPos(c - 1)
        return self.curpos
    
    def back_to_indentation(self):
        self.ScrollToColumn(0)
        self.GotoPos(self.bol)
        return self.skip_chars_forward(r'\s')
    
    def beggining_of_line(self):
        self.GotoPos(self.bol)
        self.ScrollToColumn(0)
        return self.curpos
    
    def end_of_line(self):
        self.GotoPos(self.eol)
        return self.curpos
    
    def goto_matched_paren(self):
        p = self.right_paren
        if p != -1:
            return self.GotoPos(p+1)
        p = self.left_paren
        if p != -1:
            return self.GotoPos(p)
        q = self.right_quotation
        if q != -1:
            return self.GotoPos(q)
        q = self.left_quotation
        if q != -1:
            return self.GotoPos(q)
    
    def selection_forward_word_or_paren(self):
        p = self.right_paren
        if p != -1:
            return self.SetCurrentPos(p+1) # forward selection to parenthesized words
        q = self.right_quotation
        if q != -1:
            return self.SetCurrentPos(q) # forward selection to quoted words
        self.WordRightEndExtend()  # otherwise, extend selection forward word
    
    def selection_backward_word_or_paren(self):
        p = self.left_paren
        if p != -1:
            return self.SetCurrentPos(p) # backward selection to parenthesized words
        q = self.left_quotation
        if q != -1:
            return self.SetCurrentPos(q) # forward selection to quoted words
        self.WordLeftExtend() # otherwise, extend selection backward word
    
    def get_selection_or_topic(self):
        """Selected substring or topic word at the caret
        Note: there is no specific definition of the `word` boundary.
        """
        topic = self.SelectedText
        if topic:
            return topic
        with self.save_excursion():
            boundaries = "({[<>]}),:;"
            p = q = self.curpos
            c = self.preceding_char
            if not c.isspace() and c not in boundaries:
                self.WordLeft()
                p = self.curpos
            c = self.following_char
            if not c.isspace() and c not in boundaries:
                self.WordRightEnd()
                q = self.curpos
            return self.GetTextRange(p, q)
    
    def save_excursion(self):
        class Excursion(object):
            def __init__(self, win):
                self._win = win
            
            def __enter__(self):
                self.pos = self._win.curpos
                self.vpos = self._win.GetScrollPos(wx.VERTICAL)
                self.hpos = self._win.GetScrollPos(wx.HORIZONTAL)
            
            def __exit__(self, t, v, tb):
                self._win.GotoPos(self.pos)
                self._win.ScrollToLine(self.vpos)
                self._win.SetXOffset(self.hpos)
            
        return Excursion(self)
    
    ## --------------------------------
    ## Edit /eat /kill
    ## --------------------------------
    
    def clear(self):
        """Delete all text"""
        self.ClearAll()
    
    @editable
    def eat_white_forward(self):
        p = self.curpos
        q = self.skip_chars_forward(r'\s')
        self.Replace(p, q, '')
    
    @editable
    def eat_white_backward(self):
        p = self.curpos
        q = self.skip_chars_backward(r'\s')
        self.Replace(max(q, self.bol), p, '')
    
    @editable
    def kill_line(self):
        p = self.eol
        text, lp = self.CurLine
        if p == self.curpos:
            if self.GetTextRange(p, p+1) == '\r': p += 1
            if self.GetTextRange(p, p+1) == '\n': p += 1
        self.Replace(self.curpos, p, '')
    
    @editable
    def backward_kill_line(self):
        p = self.bol
        text, lp = self.CurLine
        if text[:lp] == sys.ps2: # caret at the prompt head
            p -= len(sys.ps2)
            lp -= len(sys.ps2)
        if text[:lp] == '' and p: # caret at the beginning of the line
            if self.GetTextRange(p-1, p) == '\n': p -= 1
            if self.GetTextRange(p-1, p) == '\r': p -= 1
        self.Replace(p, self.curpos, '')
    
    @editable
    def insert_space_like_tab(self):
        """Enter half-width spaces forward as if feeling like a tab
        タブの気持ちになって半角スペースを前向きに入力する
        """
        self.eat_white_forward()
        text, lp = self.CurLine
        self.WriteText(' ' * (4 - lp % 4))
    
    @editable
    def delete_backward_space_like_tab(self):
        """Delete half-width spaces backward as if feeling like a S-tab
        シフト+タブの気持ちになって半角スペースを後ろ向きに消す
        """
        self.eat_white_forward()
        text, lp = self.CurLine
        for i in range(lp % 4 or 4):
            p = self.curpos
            if self.preceding_char != ' ' or p == self.bol:
                break
            self.curpos = p-1
        self.ReplaceSelection('')


class Editor(EditWindow, EditorInterface):
    """Python code editor
    """
    parent = property(lambda self: self.__parent)
    message = property(lambda self: self.__parent.message)
    
    def load(self, filename, lineno=0):
        if filename is None:
            self.target = None
            return False
        m = re.match("(.*?):([0-9]+)", filename) # @where
        if m:
            filename, ln = m.groups()
            lineno = int(ln)
        lines = linecache.getlines(filename)
        if lines:
            self.Text = ''.join(lines)
            self.target = filename
            if lineno:
                self.mark = self.PositionFromLine(lineno-1)
                self.goto_char(self.mark)
                wx.CallAfter(self.recenter)
            return True
        return False
    
    PALETTE_STYLE = { #<Editor>
        "STC_STYLE_DEFAULT"     : "fore:#000000,back:#ffffb8,face:MS Gothic,size:9",
        "STC_STYLE_CARETLINE"   : "fore:#000000,back:#ffff7f,size:2",
        "STC_STYLE_LINENUMBER"  : "fore:#000000,back:#ffffb8,size:9",
        "STC_STYLE_BRACELIGHT"  : "fore:#000000,back:#ffffb8,bold",
        "STC_STYLE_BRACEBAD"    : "fore:#000000,back:#ff0000,bold",
        "STC_STYLE_CONTROLCHAR" : "size:9",
        "STC_P_DEFAULT"         : "fore:#000000,back:#ffffb8",
        "STC_P_IDENTIFIER"      : "fore:#000000",
        "STC_P_COMMENTLINE"     : "fore:#007f7f,back:#ffcfcf",
        "STC_P_COMMENTBLOCK"    : "fore:#007f7f,back:#ffcfcf,eol",
        "STC_P_CHARACTER"       : "fore:#7f7f7f",
        "STC_P_STRING"          : "fore:#7f7f7f",
        "STC_P_TRIPLE"          : "fore:#7f7f7f,eol",
        "STC_P_TRIPLEDOUBLE"    : "fore:#7f7f7f,eol",
        "STC_P_STRINGEOL"       : "fore:#7f7f7f",
        "STC_P_WORD"            : "fore:#0000ff",
        "STC_P_WORD2"           : "fore:#b8007f",
        "STC_P_WORD3"           : "fore:#ff0000,back:#ffff00", # optional for search word
        "STC_P_DEFNAME"         : "fore:#0000ff,bold",
        "STC_P_CLASSNAME"       : "fore:#0000ff,bold",
        "STC_P_DECORATOR"       : "fore:#e08040",
        "STC_P_OPERATOR"        : "",
        "STC_P_NUMBER"          : "fore:#7f0000",
    }
    
    def __init__(self, parent, **kwargs):
        EditWindow.__init__(self, parent, **kwargs)
        EditorInterface.__init__(self)
        
        self.__parent = parent #= self.Parent, but not always if whose son is floating
        
        self.target = None
        
        ## To prevent @filling crash (Never access to DropTarget)
        ## Don't allow DnD of text, file, whatever.
        self.SetDropTarget(None)
        
        @self.handler.bind('*button* pressed')
        @self.handler.bind('*button* released')
        def forkup(v):
            """Fork mouse events to the parent"""
            self.parent.handler(self.handler.event, v)
            v.Skip()
        
        @self.handler.bind('focus_set')
        def activate(v):
            self.parent.handler('title_window', self.target)
            self.trace_point()
            v.Skip()
        
        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdate)
        
        self.set_style(self.PALETTE_STYLE)
    
    def trace_point(self):
        text, lp = self.CurLine
        self.message("{:>6d}:{} ({})".format(self.curline, lp, self.curpos), pane=1)
    
    def OnUpdate(self, evt): #<wx._stc.StyledTextEvent>
        if evt.Updated & (stc.STC_UPDATE_SELECTION | stc.STC_UPDATE_CONTENT):
            self.trace_point()
        evt.Skip()


class Nautilus(Shell, EditorInterface):
    """Nautilus in the Shell with Editor interface

Features:
    All objects in the process can be accessed using
        self : the target of the shell
        this : the module which includes target

Magic syntax:
   quoteback : x`y --> y=x  | x`y`z --> z=y=x
    pullback : x@y --> y(x) | x@y@z --> z(y(x))
     apropos : x.y? [not] p --> shows apropos (not-)matched by predicates p
                equiv. apropos(x, y [,ignorecase ?:True,??:False] [,pred=p])
                y can contain regular expressions.
                    (RE) \\a:[a-z], \\A:[A-Z] can be used in addition.
                p can be atom, callable, type (e.g., int, str, ...),
                    and any predicates such as inspect.isclass.
  
  *     info :  ?x (x@?) --> info(x) shows short information
  *     help : ??x (x@??) --> help(x) shows full description
  *   system :  !x (x@!) --> sx(x) executes command in external shell
  
  * denotes original syntax defined in wx.py.shell,
    for which, at present version, enabled with USE_MAGIC switch being on

Shell built-in utility:
    @p          synonym of print
    @pp         synonym of pprint
    @info   @?  short info
    @help   @?? full description
    @dive       clone the shell with new target
    @timeit     measure the duration cpu time
    @profile    profile the func(*args, **kwargs)
    @filling    inspection using wx.lib.filling.Filling
    @watch      inspection using wx.lib.inspection.InspectionTool
    @edit       open file with your editor (undefined)
    @where      filename and lineno or module
    @debug      open pdb or show event-watcher and widget-tree

Autocomp key bindings:
        C-up : [0] retrieve previous history
      C-down : [0] retrieve next history
    M-j, C-j : [0] call tooltip of eval (for the word selected or focused)
    M-h, C-h : [0] call tooltip of help (for the func selected or focused)
         TAB : [1] history-comp-mode
         M-p : [1] retrieve previous history in comp-mode
         M-n : [1] retrieve next history in comp-mode
         M-. : [2] word-comp-mode
         M-/ : [3] apropos-comp-mode
         M-, : [4] text-comp-mode
         M-m : [5] module-comp-mode
  * Autocomps are incremental when pressed any alnums, and decremental when backspace.

Enter key bindings:
     C-enter : insert-line-break
     M-enter : duplicate-command

This module is based on the implementation of wx.py.shell.
    Some of the original key bindings are overridden in the FSM framework.
    To read the original key bindings, see 'wx.py.shell.HELP_TEXT'.
    The original key bindings are mapped in esc-map, i.e.,
    e.g., if you want to do 'select-all', type [ESC C-a], not [C-a]

The most convenient way to see the details of keymaps on the shell:
    >>> self.shell.handler @p
     or self.shell.handler @filling

Flaky nutshell:
    With great oven by Robin Dunn,
    Half-baked by Patrik K. O'Brien,
    and the other half by K. O'moto.
    """
    parent = property(lambda self: self.__parent)
    message = property(lambda self: self.__parent.message)
    
    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self, target):
        """Reset the shell->target; Rename the parent title
        """
        if not hasattr(target, '__dict__'):
            raise TypeError("Unable to target primitive object: {!r}".format(target))
        
        ## Note: self, this, and shell are set/overwritten.
        try:
            target.self = target
            target.this = inspect.getmodule(target)
            target.shell = self # overwrite the facade <wx.py.shell.ShellFacade>
        except AttributeError as e:
            print("- cannot set target vars: {!r}".format(e))
            pass
        self.__target = target
        self.interp.locals = target.__dict__
    
    @property
    def locals(self):
        return self.interp.locals
    
    @locals.setter
    def locals(self, v): # internal use only
        self.interp.locals = v
    
    @locals.deleter
    def locals(self): # internal use only
        self.interp.locals = self.__target.__dict__
    
    @property
    def globals(self):
        return self.interp.globals
    
    @globals.setter
    def globals(self, v): # internal use only
        self.interp.globals = v
    
    @globals.deleter
    def globals(self): # internal use only
        self.interp.globals = self.__target.__dict__
    
    PALETTE_STYLE = { #<Shell>
        "STC_STYLE_DEFAULT"     : "fore:#cccccc,back:#202020,face:MS Gothic,size:9",
        "STC_STYLE_CARETLINE"   : "fore:#ffffff,back:#123460,size:2",
        "STC_STYLE_LINENUMBER"  : "fore:#000000,back:#f0f0f0,size:9",
        "STC_STYLE_BRACELIGHT"  : "fore:#ffffff,back:#202020,bold",
        "STC_STYLE_BRACEBAD"    : "fore:#ffffff,back:#ff0000,bold",
        "STC_STYLE_CONTROLCHAR" : "size:9",
        "STC_P_DEFAULT"         : "fore:#cccccc,back:#202020",
        "STC_P_IDENTIFIER"      : "fore:#cccccc",
        "STC_P_COMMENTLINE"     : "fore:#42c18c,back:#004040",
        "STC_P_COMMENTBLOCK"    : "fore:#42c18c,back:#004040,eol",
        "STC_P_CHARACTER"       : "fore:#a0a0a0",
        "STC_P_STRING"          : "fore:#a0a0a0",
        "STC_P_TRIPLE"          : "fore:#a0a0a0,back:#004040,eol",
        "STC_P_TRIPLEDOUBLE"    : "fore:#a0a0a0,back:#004040,eol",
        "STC_P_STRINGEOL"       : "fore:#808080",
        "STC_P_WORD"            : "fore:#80a0ff",
        "STC_P_WORD2"           : "fore:#ff80ff",
        "STC_P_WORD3"           : "fore:#ff0000,back:#ffff00", # optional for search word
        "STC_P_DEFNAME"         : "fore:#e0c080,bold",
        "STC_P_CLASSNAME"       : "fore:#e0c080,bold",
        "STC_P_DECORATOR"       : "fore:#e08040",
        "STC_P_OPERATOR"        : "",
        "STC_P_NUMBER"          : "fore:#ffc080",
    }
    
    modules = None
    
    def __init__(self, parent, target,
                 introText=None,
                 startupScript=None,
                 execStartupScript=True,
                 **kwargs):
        Shell.__init__(self, parent,
                 locals=target.__dict__,
                 introText=introText,
                 startupScript=startupScript,
                 execStartupScript=execStartupScript, # if True, executes ~/.py
                 **kwargs)
        EditorInterface.__init__(self)
        
        ## cf. sys.modules (shell.modules
        if not Nautilus.modules:
            force = wx.GetKeyState(wx.WXK_CONTROL)\
                  & wx.GetKeyState(wx.WXK_SHIFT)
            Nautilus.modules = ut.find_modules(force)
        
        self.__parent = parent #= self.Parent, but not always if whose son is floating
        
        self.target = target
        
        self.globals = self.locals
        self.interp.runcode = self.runcode
        
        wx.py.shell.USE_MAGIC = True
        wx.py.shell.magic = self.magic # called when USE_MAGIC
        
        ## This shell is expected to be created many times in the process,
        ## e.g., when used as a breakpoint and when cloned.
        ## Assign objects each time it is activated so that the target
        ## does not refer to dead objects in the shell clones (to be deleted).
        
        def activate(v):
            self.handler('shell_activated', self)
            self.parent.handler('title_window', self.target)
            self.trace_point()
        
        def inactivate(v):
            self.handler('shell_inactivated', self)
        
        ## EditWindow.OnUpdateUI は Shell.OnUpdateUI とかぶってオーバーライドされるので
        ## ここでは別途 EVT_STC_UPDATEUI ハンドラを追加する (EVT_UPDATE_UI ではない !)
        
        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdate) # skip to brace matching
        
        ## To prevent @filling crash (Never access to DropTarget)
        ## Don't allow DnD of text, file, whatever.
        self.SetDropTarget(None)
        
        ## some AutoComp settings
        self.AutoCompSetAutoHide(False)
        self.AutoCompSetIgnoreCase(True)
        
        def clear(v):
            ## Clear selection and statusline, no skip.
            ## *do not* clear autocomp, so that the event can skip to AutoComp properly.
            ## if self.AutoCompActive():
            ##     self.AutoCompCancel() # may delete selection
            if self.CanEdit():
                self.ReplaceSelection("")
            self.message("")
        
        def fork(v):
            self.handler(self.handler.event, v)
        
        def forkup(v):
            self.parent.handler(self.handler.event, v)
        
        self.handler.update({ #<Nautilus.handler>
            None : {
                    'focus_set' : [ None, skip, activate ],
                   'focus_kill' : [ None, skip, inactivate ],
                 'shell_cloned' : [ None, ],
              'shell_activated' : [ None, self.on_activated ],
            'shell_inactivated' : [ None, self.on_inactivated ],
              '*button* dclick' : [ None, skip, forkup ],
             '*button* pressed' : [ None, skip, forkup ],
            '*button* released' : [ None, skip, forkup ],
            },
            -1 : { # original action of the wx.py.shell
                    '* pressed' : (0, skip, lambda v: self.message("ESC {}".format(v.key))),
                 '*alt pressed' : (-1, ),
                '*ctrl pressed' : (-1, ),
               '*shift pressed' : (-1, ),
             '*[LR]win pressed' : (-1, ),
                 '*f12 pressed' : (-2, self.on_enter_notemode),
            },
            -2 : {
                  'C-g pressed' : (0, self.on_exit_notemode),
                 '*f12 pressed' : (0, self.on_exit_notemode),
               'escape pressed' : (0, self.on_exit_notemode),
            },
            0 : { # Normal mode
                    '* pressed' : (0, skip),
               'escape pressed' : (-1, self.OnEscape),
                'space pressed' : (0, self.OnSpace),
           '*backspace pressed' : (0, self.OnBackspace),
                'enter pressed' : (0, self.OnEnter),
              'C-enter pressed' : (0, _F(self.insertLineBreak)),
            'C-S-enter pressed' : (0, _F(self.insertLineBreak)),
              'M-enter pressed' : (0, _F(self.duplicate_command)),
               '*enter pressed' : (0, noskip), # -> OnShowCompHistory 無効
                 'left pressed' : (0, self.OnBackspace),
               'C-left pressed' : (0, self.OnBackspace),
                 ## 'C-up pressed' : (0, _F(self.OnHistoryReplace, step=+1, doc="prev-command")),
               ## 'C-down pressed' : (0, _F(self.OnHistoryReplace, step=-1, doc="next-command")),
               ## 'C-S-up pressed' : (0, ), # -> Shell.OnHistoryInsert(+1) 無効
             ## 'C-S-down pressed' : (0, ), # -> Shell.OnHistoryInsert(-1) 無効
                 'M-up pressed' : (0, _F(self.goto_previous_mark)),
               'M-down pressed' : (0, _F(self.goto_next_mark)),
                  'C-v pressed' : (0, _F(self.Paste)),
                'C-S-v pressed' : (0, _F(self.Paste, rectangle=1)),
             'S-insert pressed' : (0, _F(self.Paste)),
           'C-S-insert pressed' : (0, _F(self.Paste, rectangle=1)),
                  'M-j pressed' : (0, self.call_tooltip2),
                  'C-j pressed' : (0, self.call_tooltip),
                  'M-h pressed' : (0, self.call_helpTip2),
                  'C-h pressed' : (0, self.call_helpTip),
                    '. pressed' : (2, self.OnEnterDot),
                  'tab pressed' : (1, self.call_history_comp), # quit -> indent_line
                'S-tab pressed' : (0, skip),
                  'M-p pressed' : (1, self.call_history_comp),
                  'M-n pressed' : (1, self.call_history_comp),
                  'M-. pressed' : (2, self.call_word_autocomp),
                  'M-/ pressed' : (3, self.call_apropos_autocomp),
                  'M-, pressed' : (4, self.call_text_autocomp),
                  'M-m pressed' : (5, self.call_module_autocomp),
            },
            1 : { # history auto completion S-mode
                         'quit' : (0, clear, _F(self.indent_line)),
                    '* pressed' : (0, fork),
                  '*up pressed' : (1, self.on_completion_forward_history),
                '*down pressed' : (1, self.on_completion_backward_history),
               'S-left pressed' : (1, skip),
              'S-right pressed' : (1, skip),
              'shift* released' : (1, self.call_history_comp),
                  'tab pressed' : (1, self.on_completion_forward_history),
                'S-tab pressed' : (1, self.on_completion_backward_history),
                  'M-p pressed' : (1, self.on_completion_forward_history),
                  'M-n pressed' : (1, self.on_completion_backward_history),
                'enter pressed' : (0, lambda v: self.goto_char(-1)),
               'escape pressed' : (0, clear),
            '[a-z0-9_] pressed' : (1, skip),
           '[a-z0-9_] released' : (1, self.call_history_comp),
            'S-[a-z\\] pressed' : (1, skip),
           'S-[a-z\\] released' : (1, self.call_history_comp),
                  ## 'M-. pressed' : (2, clear, self.call_word_autocomp),
                  ## 'M-/ pressed' : (3, clear, self.call_apropos_autocomp),
                  ## 'M-, pressed' : (4, clear, self.call_text_autocomp),
                 '*alt pressed' : (1, ),
                '*ctrl pressed' : (1, ),
               '*shift pressed' : (1, ),
             '*[LR]win pressed' : (1, ),
             '*f[0-9]* pressed' : (1, ),
            },
            2 : { # word auto completion AS-mode
                         'quit' : (0, self.clear_autocomp),
                    '* pressed' : (0, self.clear_autocomp, fork),
                   'up pressed' : (2, self.on_completion_backward),
                 'down pressed' : (2, self.on_completion_forward),
                 'left pressed' : (2, skip),
                'right pressed' : (2, self.process_autocomp),
               'S-left pressed' : (2, skip),
              'S-right pressed' : (2, skip),
              'shift* released' : (2, self.call_word_autocomp),
                  'tab pressed' : (0, clear, skip),
                'enter pressed' : (0, clear, fork),
               'escape pressed' : (0, self.clear_autocomp),
           '[a-z0-9_.] pressed' : (2, skip),
          '[a-z0-9_.] released' : (2, self.call_word_autocomp),
            'S-[a-z\\] pressed' : (2, skip),
           'S-[a-z\\] released' : (2, self.call_word_autocomp),
              '*delete pressed' : (2, skip),
           '*backspace pressed' : (2, self.skipback_autocomp),
          '*backspace released' : (2, self.call_word_autocomp, self.decrback_autocomp),
        'C-S-backspace pressed' : (2, noskip),
                  'M-j pressed' : (2, self.call_tooltip2),
                  'C-j pressed' : (2, self.call_tooltip),
                  'M-h pressed' : (2, self.call_helpTip2),
                  'C-h pressed' : (2, self.call_helpTip),
                  ## 'M-. pressed' : (2, self.on_completion),
                  ## 'M-/ pressed' : (3, clear, self.call_apropos_autocomp),
                  ## 'M-, pressed' : (4, clear, self.call_text_autocomp),
                 '*alt pressed' : (2, ),
                '*ctrl pressed' : (2, ),
               '*shift pressed' : (2, ),
             '*[LR]win pressed' : (2, ),
             '*f[0-9]* pressed' : (2, ),
            },
            3 : { # apropos auto completion AS-mode
                         'quit' : (0, self.clear_autocomp),
                    '* pressed' : (0, self.clear_autocomp, fork),
                   'up pressed' : (3, self.on_completion_backward),
                 'down pressed' : (3, self.on_completion_forward),
                 'left pressed' : (3, skip),
                'right pressed' : (3, self.process_autocomp),
               'S-left pressed' : (3, skip),
              'S-right pressed' : (3, skip),
              'shift* released' : (3, self.call_apropos_autocomp),
                  'tab pressed' : (0, clear, skip),
                'enter pressed' : (0, clear, fork),
               'escape pressed' : (0, self.clear_autocomp),
           '[a-z0-9_.] pressed' : (3, skip),
          '[a-z0-9_.] released' : (3, self.call_apropos_autocomp),
            'S-[a-z\\] pressed' : (3, skip),
           'S-[a-z\\] released' : (3, self.call_apropos_autocomp),
              '*delete pressed' : (3, skip),
           '*backspace pressed' : (3, self.skipback_autocomp),
          '*backspace released' : (3, self.call_apropos_autocomp, self.decrback_autocomp),
        'C-S-backspace pressed' : (3, noskip),
                  'M-j pressed' : (3, self.call_tooltip2),
                  'C-j pressed' : (3, self.call_tooltip),
                  'M-h pressed' : (3, self.call_helpTip2),
                  'C-h pressed' : (3, self.call_helpTip),
                  ## 'M-. pressed' : (2, clear, self.call_word_autocomp),
                  ## 'M-/ pressed' : (3, self.on_completion),
                  ## 'M-, pressed' : (4, clear, self.call_text_autocomp),
                 '*alt pressed' : (3, ),
                '*ctrl pressed' : (3, ),
               '*shift pressed' : (3, ),
             '*[LR]win pressed' : (3, ),
             '*f[0-9]* pressed' : (3, ),
            },
            4 : { # text auto completion AS-mode
                         'quit' : (0, self.clear_autocomp),
                    '* pressed' : (0, self.clear_autocomp, fork),
                   'up pressed' : (4, self.on_completion_backward),
                 'down pressed' : (4, self.on_completion_forward),
                 'left pressed' : (4, skip),
                'right pressed' : (4, self.process_autocomp),
               'S-left pressed' : (4, skip),
              'S-right pressed' : (4, skip),
              'shift* released' : (4, self.call_text_autocomp),
                  'tab pressed' : (0, clear, skip),
                'enter pressed' : (0, clear, fork),
               'escape pressed' : (0, self.clear_autocomp),
           '[a-z0-9_.] pressed' : (4, skip),
          '[a-z0-9_.] released' : (4, self.call_text_autocomp),
            'S-[a-z\\] pressed' : (4, skip),
           'S-[a-z\\] released' : (4, self.call_text_autocomp),
              '*delete pressed' : (4, skip),
           '*backspace pressed' : (4, self.skipback_autocomp),
          '*backspace released' : (4, self.call_text_autocomp),
        'C-S-backspace pressed' : (4, noskip),
                  'M-j pressed' : (4, self.call_tooltip2),
                  'C-j pressed' : (4, self.call_tooltip),
                  'M-h pressed' : (4, self.call_helpTip2),
                  'C-h pressed' : (4, self.call_helpTip),
                  ## 'M-. pressed' : (2, clear, self.call_word_autocomp),
                  ## 'M-/ pressed' : (3, clear, self.call_apropos_autocomp),
                  ## 'M-, pressed' : (4, self.on_completion),
                 '*alt pressed' : (4, ),
                '*ctrl pressed' : (4, ),
               '*shift pressed' : (4, ),
             '*[LR]win pressed' : (4, ),
             '*f[0-9]* pressed' : (4, ),
            },
            5 : { # module auto completion AS-mode
                         'quit' : (0, self.clear_autocomp),
                    '* pressed' : (0, self.clear_autocomp, fork),
                   'up pressed' : (5, self.on_completion_backward),
                 'down pressed' : (5, self.on_completion_forward),
                 'left pressed' : (5, skip),
                'right pressed' : (5, self.process_autocomp),
               'S-left pressed' : (5, skip),
              'S-right pressed' : (5, skip),
              'shift* released' : (5, self.call_module_autocomp),
                  'tab pressed' : (0, clear, skip),
                'enter pressed' : (0, clear, fork),
               'escape pressed' : (0, self.clear_autocomp),
           '[a-z0-9_.] pressed' : (5, skip),
          '[a-z0-9_.] released' : (5, self.call_module_autocomp),
            'S-[a-z\\] pressed' : (5, skip),
           'S-[a-z\\] released' : (5, self.call_module_autocomp),
           '*backspace pressed' : (5, self.skipback_autocomp),
          '*backspace released' : (5, self.call_module_autocomp),
        'C-S-backspace pressed' : (5, noskip),
                 '*alt pressed' : (5, ),
                '*ctrl pressed' : (5, ),
               '*shift pressed' : (5, ),
             '*[LR]win pressed' : (5, ),
             '*f[0-9]* pressed' : (5, ),
            },
        })
        
        self.show_folder(True)
        self.set_style(self.PALETTE_STYLE)
        
        self.__text = ''
        self.__start = 0
    
    def trace_point(self):
        text, lp = self.CurLine
        self.message("{:>6d}:{} ({})".format(self.curline, lp, self.curpos), pane=1)
    
    def OnUpdate(self, evt): #<wx._stc.StyledTextEvent>
        if evt.Updated & (stc.STC_UPDATE_SELECTION | stc.STC_UPDATE_CONTENT):
            self.trace_point()
            if self.handler.current_state == 0:
                text = self.expr_at_caret
                if text != self.__text:
                    name, argspec, tip = self.interp.getCallTip(text)
                    if tip:
                        tip = tip.splitlines()[0]
                    self.message(tip)
                    self.__text = text
        evt.Skip()
    
    ## --------------------------------
    ## Special keymap of the shell
    ## --------------------------------
    
    def OnEscape(self, evt):
        """Called when escape pressed"""
        if self.AutoCompActive():
            self.AutoCompCancel()
        if self.CallTipActive():
            self.CallTipCancel()
        ## if self.eolc < self.bolc: # check if prompt is in valid state
        ##     self.prompt() # ここでは機能しない？
        ##     evt.Skip()
        self.message("ESC-")
    
    def OnSpace(self, evt):
        """Called when space pressed"""
        if not self.CanEdit():
            return
        
        cmdl = self.cmdlc
        if re.match(r"(import|from)\s*$", cmdl)\
        or re.match(r"from\s+([\w.]+)\s+import\s*$", cmdl):
            self.ReplaceSelection(' ')
            self.handler('M-m pressed', None) # call_module_autocomp
            return
        evt.Skip()
    
    def OnBackspace(self, evt):
        """Called when backspace (or *left) pressed
        Backspace-guard from Autocomp eating over a prompt white
        """
        if self.curpos == self.bolc:
            ## do not skip to prevent autocomp eats prompt,
            ## so not to backspace over the latest non-continuation prompt
            return
        evt.Skip()
    
    def OnEnter(self, evt):
        """Called when enter pressed"""
        if not self.CanEdit(): # go back to the end of command line
            self.goto_char(-1)
            if self.eolc < self.bolc: # check if prompt is in valid state
                self.prompt()
                evt.Skip()
            return
        
        if self.AutoCompActive(): # skip to auto completion
            evt.Skip()
            return
        
        if self.CallTipActive():
            self.CallTipCancel()
        
        text = self.cmdline
        
        ## skip to wx.py.magic if text begins with !(sx), ?(info), and ??(help)
        if not text or text[0] in '!?':
            evt.Skip()
            return
        
        tokens = ut.split_words(text)
        
        ## cast magic for `@? (Note: PY35 supports @(matmal)-operator)
        if any(x in tokens for x in '`@?$'):
            cmd = self.magic_interpret(tokens)
            if '\n' in cmd:
                self.Execute(cmd) # for multi-line commands
            else:
                self.run(cmd, verbose=0, prompt=0) # => push(cmd)
            return
        
        ## normal execute/run
        if '\n' in text:
            self.Execute(text) # for multi-line commands
        else:
            evt.Skip()
    
    def OnEnterDot(self, evt):
        """Called when dot(.) pressed"""
        sep = "`@=+-/*%<>&|^~,:; \t\r\n!?([{" # OPS; SEPARATOR_CHARS; !? and open-parens
        
        if not self.CanEdit():
            return
        
        st = self.GetStyleAt(self.curpos-1)
        
        if self.following_char.isalnum(): # e.g., self[.]abc, 0[.]123, etc.,
            self.handler('quit', evt)
            pass
        elif st in (1,2,5,8,9,12): # comment, num, word, class, def
            self.handler('quit', evt)
            pass
        elif st in (3,4,6,7,13): # string, char, triplet, eol
            pass
        elif self.preceding_symbol in sep:
            self.ReplaceSelection("self")
        
        self.ReplaceSelection('.') # just write down a dot.
        evt.Skip(False)            # and do not skip to default autocomp mode
    
    def duplicate_command(self, clear=True):
        if self.CanEdit():
            return
        cmd = self.getMultilineCommand() # Don't use in prompt
        if cmd:
            if clear:
                self.clearCommand()
            self.write(cmd, -1)
    
    def on_enter_notemode(self, evt):
        self.noteMode = True
        self.SetCaretForeground("red")
        self.SetCaretWidth(4)
    
    def on_exit_notemode(self, evt):
        self.noteMode = False
        self.set_style(self.PALETTE_STYLE)
        ## self.goto_char(-1)
        ## self.prompt()
        self.promptPosEnd = self.TextLength
    
    ## --------------------------------
    ## Magic caster of the shell
    ## --------------------------------
    
    @staticmethod
    def magic(cmd):
        """Called before command pushed
        (override) with magic: f x --> f(x) disabled
        """
        if cmd:
            if cmd[0:2] == '??': cmd = 'help({})'.format(cmd[2:])
            elif cmd[0] == '?': cmd = 'info({})'.format(cmd[1:])
            elif cmd[0] == '!': cmd = 'sx({!r})'.format(cmd[1:])
        return cmd
    
    def magic_interpret(self, tokens):
        """Called when [Enter] command, or eval-time for tooltip
        Interpret magic syntax
           quoteback : x`y --> y=x
            pullback : x@y --> y(x)
             partial : x@(y1,...,yn) --> partial(y1,...,yn)(x)
             apropos : x.y?p --> apropos(x,y,...,p)
        
        Note: This is called before run, execute, and original magic.
        """
        sep1 = "`@=+-/*%<>&|^~;\t\r\n"   # [`] SEPARATOR_CHARS; nospace, nocomma
        sep2 = "`@=+-/*%<>&|^~;, \t\r\n" # [@] SEPARATOR_CHARS;
        
        def _eats(r, sep):
            s = ''
            while r and r[0].isspace(): # skip whites
                r.pop(0)
            while r and r[0] not in sep: # eat until seps appear
                s += r.pop(0)
            return ''.join(s)
        
        lhs = ''
        for i, c in enumerate(tokens):
            rs = tokens[i+1:]
            
            if c == '@':
                f = "{rhs}({lhs})"
                lhs = lhs.strip() or '_'
                rhs = _eats(rs, sep2).strip()
                rhs = re.sub(r"^(\(.*\))$",     # x@(y1,...,yn)
                             r"partial\1", rhs) # --> partial(y1,...,yn)(x)
                return self.magic_interpret([f.format(lhs=lhs, rhs=rhs)] + rs)
            
            if c == '`':
                f = "{rhs}={lhs}"
                lhs = lhs.strip() or '_'
                rhs = _eats(rs, sep1).strip()
                return self.magic_interpret([f.format(lhs=lhs, rhs=rhs)] + rs)
            
            if c == '?':
                head, sep, hint = lhs.rpartition('.')
                cc, pred = re.search(r"(\?+)\s*(.*)", c+''.join(rs)).groups()
                return ("apropos({0}, {1!r}, ignorecase={2}, alias={0!r}, "
                        "pred={3!r}, locals=locals())".format(
                        head, hint.strip(), len(cc)<2, pred or None))
            
            if c == sys.ps2.strip():
                while rs and rs[0].isspace(): # eat whites
                    c += rs.pop(0)
                return lhs + c + self.magic_interpret(rs)
            
            if c in ';\r\n':
                return lhs + c + self.magic_interpret(rs)
            
            lhs += c
        return ''.join(tokens)
    
    def setBuiltinKeywords(self):
        """Create pseudo keywords as part of builtins (override)"""
        Shell.setBuiltinKeywords(self)
        
        ## Add more useful global abbreviations to builtins
        builtins.typename = typename
        builtins.apropos = apropos
        builtins.reload = reload
        builtins.partial = partial
        builtins.p = print
        builtins.pp = pp
        builtins.mro = mro
        builtins.where = where
        builtins.watch = watchit
        builtins.filling = filling
    
    def on_activated(self, shell):
        """Called when shell:self is activated
        Reset localvars and builtins assigned for the shell->target.
        Note: the target could be referred from other shells.
        """
        ## self.target = shell.target # => @target.setter !! Don't overwrite locals here
        try:
            self.target.shell = self # overwrite the facade <wx.py.shell.ShellFacade>
        except AttributeError as e:
            print("- cannot set target vars: {!r}".format(e))
            pass
        
        ## To prevent the builtins from referring dead objects,
        ## Add utility functions to builtins each time when activated.
        builtins.help = self.help
        builtins.info = self.info
        builtins.dive = self.clone
        builtins.timeit = self.timeit
        builtins.profile = self.profile
        try:
            builtins.debug = self.parent.debug
        except AttributeError:
            builtins.debug = monitor
        
    def on_inactivated(self, shell):
        """Called when shell:self is inactivated
        Remove target localvars and builtins assigned for the shell->target.
        """
        if self.AutoCompActive():
            self.AutoCompCancel()
        if self.CallTipActive():
            self.CallTipCancel()
        try:
            del builtins.help
            del builtins.info
            del builtins.dive
            del builtins.timeit
            del builtins.profile
            del builtins.debug
        except AttributeError:
            pass
    
    def on_text_input(self, text):
        """Called when [Enter] text (before push)
        Mark points, reset history point, etc.
        
        Note: text is raw input:str with no magic cast
        """
        if text.rstrip():
            self.__eolc_mark = self.eolc
            self.historyIndex = -1
    
    def on_text_output(self, text):
        """Called when [Enter] text (after push)
        Set markers at the last command line.
        
        Note: text is raw output:str with no magic cast
        """
        ln = self.LineFromPosition(self.bolc)
        err = re.findall(r"File \".*\", line ([0-9]+)", text, re.I)
        if not err:
            self.MarkerAdd(ln, 1) # white-arrow
        else:
            self.MarkerAdd(ln, 2) # error-arrow
        return (not err)
    
    ## --------------------------------
    ## Attributes of the shell
    ## --------------------------------
    fragmwords = set(keyword.kwlist + wdir(builtins)) # to be used in text-autocomp
    
    ## shell.history is an instance variable of the Shell.
    ## If del shell.history, the history of the class variable is used
    history = []
    
    def push(self, command, **kwargs):
        """Send command to the interpreter for execution.
        (override) mark points before push.
        """
        try:
            self.on_text_input(command)
        except AttributeError:
            pass
        Shell.push(self, command, **kwargs)
    
    def addHistory(self, command):
        """Add command to the command history
        (override) if the command is new (i.e., not found in the head of the list).
        Then, write the command to History buffer.
        """
        if not command:
            return
        
        ## この段階では push された直後で，次のようになっている
        ## bolc : beginning of command-line
        ## eolc : end of the output-buffer
        try:
            input = self.GetTextRange(self.bolc, self.__eolc_mark)
            output = self.GetTextRange(self.__eolc_mark, self.eolc)
            
            input = self.regulate_cmd(input).lstrip()
            repeat = (self.history and self.history[0] == input)
            if not repeat and input:
                Shell.addHistory(self, input)
            
            noerr = self.on_text_output(output)
            if noerr:
                words = re.findall(r"\b[a-zA-Z_][\w.]+", input + output)
                self.fragmwords |= set(words)
            self.parent.handler('add_history', command + os.linesep, noerr)
        except AttributeError:
            ## execStartupScript 実行時は出力先 (owner) が存在しないのでパス
            ## shell.__init__ で定義するアトリビュートも存在しない
            pass
    
    @staticmethod
    def regulate_cmd(text):
        lf = '\n'
        return (text.replace(os.linesep + sys.ps1, lf)
                    .replace(os.linesep + sys.ps2, lf)
                    .replace(os.linesep, lf))
    
    def goto_previous_mark(self):
        ln = self.MarkerPrevious(self.curline-1, 1<<1)
        if ln != -1:
            self.goto_char(self.PositionFromLine(ln) + len(sys.ps1))
        else:
            self.goto_char(0)
    
    def goto_next_mark(self):
        ln = self.MarkerNext(self.curline+1, 1<<1)
        if ln != -1:
            self.goto_char(self.PositionFromLine(ln) + len(sys.ps1))
        else:
            self.goto_char(-1)
    
    def clear(self):
        """Delete all text (override) and put new prompt"""
        self.ClearAll()
        
        self.promptPosStart = 0
        self.promptPosEnd = 0
        self.more = False
        self.prompt()
    
    def write(self, text, pos=None):
        """Display text in the shell (override) :option pos"""
        if pos is not None:
            self.goto_char(pos)
        if self.CanEdit():
            Shell.write(self, text)
    
    def wrap(self, mode=1):
        """Sets whether text is word wrapped (override) with
        mode in {0:no-wrap, 1:word-wrap (2:no-word-wrap), None:toggle}
        """
        EditorInterface.wrap(self, mode)
    
    ## input = classmethod(Shell.ask)
    
    bolc = property(lambda self: self.promptPosEnd, doc="beginning of command-line")
    eolc = property(lambda self: self.TextLength, doc="end of command-line")
    
    @property
    def bol(self):
        """beginning of line (override) excluding prompt"""
        text, lp = self.CurLine
        for p in (sys.ps1, sys.ps2, sys.ps3):
            if text.startswith(p):
                lp -= len(p)
                break
        return (self.curpos - lp)
    
    ## cf. getCommand(), getMultilineCommand() -> caret-line-text that has a prompt (>>>)
    
    @property
    def cmdlc(self):
        """cull command-line (with no prompt)"""
        return self.GetTextRange(self.bol, self.curpos)
    
    @property
    def cmdline(self):
        """full command-(multi-)line (with no prompt)"""
        return self.GetTextRange(self.bolc, self.eolc)
    
    ## --------------------------------
    ## Utility functions of the shell 
    ## --------------------------------
    
    def about(self):
        """About the shell (to be overridden)"""
        print("#<module 'mwx' from {!r}>".format(__file__),
              "Author: {!r}".format(__author__),
              "Version: {!s}".format(__version__),
              "#{!r}".format(wx.py.shell),
            sep='\n')
        Shell.about(self)
    
    def Paste(self, rectangle=False):
        """Replace selection with clipboard contents.
        (override) Remove ps1 and ps2 from the multi-line command to paste.
                   Add offset for paste-rectangle mode.
        """
        if self.CanPaste() and wx.TheClipboard.Open():
            data = wx.TextDataObject()
            if wx.TheClipboard.GetData(data):
                self.ReplaceSelection('')
                text = data.GetText()
                text = self.lstripPrompt(text)
                text = self.fixLineEndings(text)
                command = self.regulate_cmd(text)
                offset = ''
                if rectangle:
                    text, lp = self.CurLine
                    offset = ' ' * (lp - len(sys.ps2))
                self.write(command.replace('\n', os.linesep + sys.ps2 + offset))
            wx.TheClipboard.Close()
    
    def info(self, obj=None):
        """Short information"""
        if obj is None:
            obj = self
        doc = inspect.getdoc(obj)\
                or "No information about {}".format(obj)
        self.parent.handler('put_help', doc) or print(doc)
    
    def help(self, obj=None):
        """Full description"""
        ## if obj is None:
        ##     self.message("The stream is piped from stdin.")
        ##     wx.CallAfter(pydoc.help)
        ##     return
        doc = pydoc.plain(pydoc.render_doc(obj))\
                or "No description about {}".format(obj)
        self.parent.handler('put_help', doc) or print(doc)
    
    def eval(self, text):
        return eval(text, self.globals, self.locals)
    
    def runcode(self, code):
        ## Monkey-patch for wx.py.interpreter.runcode
        try:
            exec(code, self.globals, self.locals)
        except Exception:
            self.interp.showtraceback()
    
    def execStartupScript(self, startupScript):
        """Execute the user's PYTHONSTARTUP script if they have one.
        (override) Add globals when executing the script
        """
        self.globals = self.locals
        Shell.execStartupScript(self, startupScript)
    
    def Execute(self, text):
        """Replace selection with text, run commands,
        (override) and check the clock time
        (patch) `finally` miss-indentation
        """
        self.__start = self.clock()
        
        ## *** The following code is a modification of <wx.py.shell.Shell.Execute>
        ##     We override (and simplified) it to make up for missing `finally`.
        lf = '\n'
        text = self.fixLineEndings(text)
        text = self.lstripPrompt(text)
        text = self.regulate_cmd(text)
        commands = []
        c = ''
        for line in text.split(lf):
            lstr = line.lstrip()
            if (lstr and lstr == line and not any(
                lstr.startswith(x) for x in ('else', 'elif', 'except', 'finally'))):
                if c:
                    commands.append(c) # Add the previous command to the list
                c = line
            else:
                c += lf + line # Multiline command. Add to the command
        commands.append(c)
        
        self.Replace(self.bolc, self.eolc, '')
        for c in commands:
            self.write(c.replace(lf, os.linesep + sys.ps2))
            self.processLine()
    
    def run(self, command, prompt=True, verbose=True):
        """Execute command as if it was typed in directly
        (override) and check the clock time
        """
        self.__start = self.clock()
        
        return Shell.run(self, command, prompt, verbose)
    
    @staticmethod
    def clock():
        try:
            return time.perf_counter()
        except AttributeError:
            return time.clock()
    
    def timeit(self, *args, **kwargs):
        t = self.clock()
        print("... duration time: {:g} s".format(t-self.__start), file=self)
    
    def profile(self, obj, *args, **kwargs):
        from profile import Profile
        pr = Profile()
        pr.runcall(obj, *args, **kwargs)
        pr.print_stats()
    
    def clone(self, target):
        if not hasattr(target, '__dict__'):
            raise TypeError("Unable to target primitive object: {!r}".format(target))
        
        ## Make shell:clone in the console
        shell = Nautilus(self.parent, target, style=wx.BORDER_NONE)
        self.parent.handler('add_page', shell, typename(target), show=True)
        self.handler('shell_cloned', shell)
        return shell
    
    ## --------------------------------
    ## Auto-comp actions of the shell
    ## --------------------------------
    
    def CallTipShow(self, pos, tip):
        """Show a call tip containing a definition near position pos.
        (override) Snip it if the tip is too big
        """
        N = 11
        lines = tip.splitlines()
        if len(lines) > N:
            lines[N+1:] = ["\n...(snip) This tips are too long..."
                          #"Show Help buffer for more details..."
                          ]
        Shell.CallTipShow(self, pos, '\n'.join(lines))
    
    def gen_autocomp(self, offset, words):
        """Call AutoCompShow for the specified words"""
        listr = ' '.join(words) # make itemlist:str
        if listr:
            self.AutoCompShow(offset, listr)
    
    def gen_tooltip(self, text):
        """Call ToolTip of the selected word or focused line"""
        if self.CallTipActive():
            self.CallTipCancel()
        try:
            tokens = ut.split_words(text)
            cmd = self.magic_interpret(tokens)
            obj = self.eval(cmd)
            text = cmd
        except Exception:
            obj = self.eval(text)
        tip = pformat(obj)
        self.CallTipShow(self.curpos, tip)
        self.message(text)
    
    def call_tooltip2(self, evt):
        """Call ToolTip of the selected word or repr"""
        try:
            text = self.SelectedText or self.expr_at_caret
            self.gen_tooltip(text)
        except Exception as e:
            self.message("- {}: {!r}".format(e, text))
    
    def call_tooltip(self, evt):
        """Call ToolTip of the selected word or command line"""
        try:
            text = self.SelectedText or self.getCommand()
            self.gen_tooltip(text)
        except Exception as e:
            self.call_tooltip2(evt)
    
    def call_helpTip2(self, evt):
        try:
            text = self.SelectedText or self.expr_at_caret
            if text:
                self.help(self.eval(text))
        except Exception as e:
            self.message("- {} : {!r}".format(e, text))
    
    def call_helpTip(self, evt):
        """Show tooltips for the selected topic"""
        if self.CallTipActive():
            self.CallTipCancel()
        self.OnCallTipAutoCompleteManually(True) # autoCallTipShow or autoCompleteShow
        if not self.CallTipActive():
            text = self.SelectedText or self.expr_at_caret
            if text:
                self.autoCallTipShow(text, False, True)
    
    def clear_autocomp(self, evt):
        """Clear Autocomp, selection, and message"""
        if self.AutoCompActive():
            self.AutoCompCancel()
        if self.CanEdit():
            self.ReplaceSelection("")
        self.message("")
    
    def skipback_autocomp(self, evt):
        """Don't eat backward prompt white"""
        if self.curpos == self.bolc:
            ## Do not skip to prevent autocomp eats prompt
            ## so not to backspace over the latest non-continuation prompt
            self.handler('quit', evt)
        evt.Skip()
    
    def decrback_autocomp(self, evt):
        """Move anchor to the word right during autocomp"""
        c = self.curpos
        if self.following_char.isalnum() and self.preceding_char == '.':
            self.WordRight()
            self.curpos = c # backward selection to anchor point
        evt.Skip()
    
    def process_autocomp(self, evt):
        """Feel like pressing {tab}"""
        if self.AutoCompActive():
            wx.UIActionSimulator().KeyDown(wx.WXK_TAB)
        else:
            evt.Skip()
    
    def on_completion_forward(self, evt):
        if self.AutoCompActive():
            self.on_completion(evt, 1)
        else:
            self.handler('quit', evt)
        evt.Skip()
    
    def on_completion_backward(self, evt):
        if self.AutoCompActive():
            self.on_completion(evt, -1)
        else:
            self.handler('quit', evt)
        evt.Skip()
    
    def on_completion_forward_history(self, evt):
        self.on_completion(evt, 1) # 古いヒストリへ進む
    
    def on_completion_backward_history(self, evt):
        self.on_completion(evt, -1) # 新しいヒストリへ戻る
    
    @postcall
    def on_completion(self, evt, step=0):
        """Show completion with selection"""
        try:
            N = len(self.__comp_words)
            j = self.__comp_ind + step
            j = 0 if j < 0 else j if j < N else N-1
            word = self.__comp_words[j]
            n = len(self.__comp_hint)
            c = self.curpos
            self.ReplaceSelection(word[n:]) # 選択された範囲を変更する(または挿入する)
            self.curpos = c # backward selection to anchor point
            self.__comp_ind = j
        except IndexError:
            self.message("no completion words")
    
    def call_history_comp(self, evt):
        """Called when history-comp mode"""
        if not self.CanEdit():
            self.handler('quit', evt)
            return
        try:
            cmdl = self.cmdlc
            if cmdl.isspace() or self.bol != self.bolc:
                self.handler('quit', evt)
                return
            
            hint = cmdl.strip()
            ls = [x.replace('\n', os.linesep + sys.ps2)
                    for x in self.history if x.startswith(hint)] # case-sensitive match
            words = sorted(set(ls), key=ls.index, reverse=0)     # keep order, no duplication
            
            self.__comp_ind = 0
            self.__comp_hint = hint
            self.__comp_words = words
            self.on_completion(evt) # show completion always
            
            ## the latest history stacks in the head of the list (time-descending)
            self.message("[history] {} candidates matched"
                         " with {!r}".format(len(words), hint))
        except Exception:
            raise
    
    def call_text_autocomp(self, evt):
        """Called when text-comp mode"""
        if not self.CanEdit():
            self.handler('quit', evt)
            return
        try:
            cmdl = self.cmdlc
            hint = re.search(r"[\w.]*$", cmdl).group(0) # get the last word or ''
            
            ls = [x for x in self.fragmwords if x.startswith(hint)] # case-sensitive match
            words = sorted(ls, key=lambda s:s.upper())
            j = 0 if words else -1
            
            self.__comp_ind = j
            self.__comp_hint = hint
            self.__comp_words = words
            
            self.gen_autocomp(len(hint), words)
            self.message("[text] {} candidates matched"
                         " with {!r}".format(len(words), hint))
        except Exception:
            raise
    
    def call_module_autocomp(self, evt):
        """Called when module-comp mode"""
        if not self.CanEdit():
            self.handler('quit', evt)
            return
        try:
            cmdl = self.cmdlc
            hint = re.search(r"[\w.]*$", cmdl).group(0) # get the last word or ''
            
            m = re.match(r"from\s+([\w.]+)\s+import\s+(.*)", cmdl)
            if m:
                text = m.group(1)
                modules = [x[len(text)+1:] for x in self.modules if x.startswith(text)]
                modules = [x for x in modules if x and '.' not in x]
            else:
                m = re.match(r"(import|from)\s+(.*)", cmdl)
                if m:
                    if not hint:
                        return
                    text = '.'
                    modules = self.modules
                else:
                    text, sep, hint = self.get_words_hint(cmdl)
                    obj = self.eval(text or 'self')
                    ## modules = [k for k,v in inspect.getmembers(obj, inspect.ismodule)]
                    modules = [k for k,v in vars(obj).items() if inspect.ismodule(v)]
            
            P = re.compile(hint)
            p = re.compile(hint, re.I)
            words = sorted([x for x in modules if p.match(x)], key=lambda s:s.upper())
            
            j = next((k for k, w in enumerate(words) if P.match(w)),
                next((k for k, w in enumerate(words) if p.match(w)), -1))
            
            self.__comp_ind = j
            self.__comp_hint = hint
            self.__comp_words = words
            
            self.gen_autocomp(len(hint), words)
            self.message("[module] {} candidates matched"
                         " with {!r} in {}".format(len(words), hint, text))
        except re.error as e:
            self.message("- re:miss compilation {!r} : {!r}".format(e, hint))
        except Exception as e:
            self.message("- {} : {!r}".format(e, text))
    
    def call_word_autocomp(self, evt):
        """Called when word-comp mode"""
        if not self.CanEdit():
            self.handler('quit', evt)
            return
        try:
            text, sep, hint = self.get_words_hint(self.cmdlc)
            obj = self.eval(text)
            
            if isinstance(obj, (bool,int,float,type(None))):
                ## self.message("- Nothing to complete")
                self.handler('quit', evt)
                return
            
            P = re.compile(hint)
            p = re.compile(hint, re.I)
            words = sorted([x for x in wdir(obj) if p.match(x)], key=lambda s:s.upper())
            
            j = next((k for k, w in enumerate(words) if P.match(w)),
                next((k for k, w in enumerate(words) if p.match(w)), -1))
            
            self.__comp_ind = j
            self.__comp_hint = hint
            self.__comp_words = words
            
            self.gen_autocomp(len(hint), words)
            self.message("[word] {} candidates matched"
                         " with {!r} in {}".format(len(words), hint, text))
        except re.error as e:
            self.message("- re:miss compilation {!r} : {!r}".format(e, hint))
        except Exception as e:
            self.message("- {} : {!r}".format(e, text))
    
    def call_apropos_autocomp(self, evt):
        """Called when apropos mode"""
        if not self.CanEdit():
            self.handler('quit', evt)
            return
        try:
            text, sep, hint = self.get_words_hint(self.cmdlc)
            obj = self.eval(text)
            
            if isinstance(obj, (bool,int,float,type(None))):
                ## self.message("- Nothing to complete")
                self.handler('quit', evt)
                return
            
            P = re.compile(hint)
            p = re.compile(hint, re.I)
            words = sorted([x for x in wdir(obj) if p.search(x)], key=lambda s:s.upper())
            
            j = next((k for k, w in enumerate(words) if P.match(w)),
                next((k for k, w in enumerate(words) if p.match(w)), -1))
            
            self.__comp_ind = j
            self.__comp_hint = hint
            self.__comp_words = words
            
            self.gen_autocomp(len(hint), words)
            self.message("[apropos] {} candidates matched"
                         " with {!r} in {}".format(len(words), hint, text))
        except re.error as e:
            self.message("- re:miss compilation {!r} : {!r}".format(e, hint))
        except Exception as e:
            self.message("- {} : {!r}".format(e, text))
    
    @staticmethod
    def get_words_hint(cmd):
        text = ut._get_words_backward(cmd)
        return text.rpartition('.') # -> text, sep, hint


## Monkey-patch for wx.core
try:
    from wx import core # PY3

    def _EvtHandler_Bind(self, event, handler=None, source=None, id=wx.ID_ANY, id2=wx.ID_ANY):
        """
        Bind an event to an event handler.
        (override) to recode and return handler
        """
        assert isinstance(event, wx.PyEventBinder)
        assert source is None or hasattr(source, 'GetId')
        if handler is None:
            return lambda f: _EvtHandler_Bind(self, event, f, source, id, id2)
        if source is not None:
            id  = source.GetId()
        event.Bind(self, id, id2, handler)
        ## record all handlers: single state machine
        if not hasattr(self, '__event_handler__'):
            self.__event_handler__ = {}
        if event.typeId not in self.__event_handler__:
            self.__event_handler__[event.typeId] = [handler]
        else:
            self.__event_handler__[event.typeId].insert(0, handler)
        return handler
    
    core.EvtHandler.Bind = _EvtHandler_Bind
    ## del _EvtHandler_Bind

    def _EvtHandler_Unbind(self, event, source=None, id=wx.ID_ANY, id2=wx.ID_ANY, handler=None):
        """
        Disconnects the event handler binding for event from `self`.
        Returns ``True`` if successful.
        (override) to remove handler
        """
        if source is not None:
            id  = source.GetId()
        retval = event.Unbind(self, id, id2, handler)
        ## remove the specified handler or all handlers
        if retval:
            try:
                actions = self.__event_handler__[event.typeId]
                if handler is None:
                    actions.clear()
                else:
                    actions.remove(handler)
                if not actions:
                    del self.__event_handler__[event.typeId]
            except Exception:
                pass
        return retval
    
    core.EvtHandler.Unbind = _EvtHandler_Unbind
    ## del _EvtHandler_Unbind

    del core

except ImportError as e:
    print("- {!r}".format(e))
    print("Python {}".format(sys.version))
    print("wxPython {}".format(wx.version()))
    pass


def deb(target=None, app=None, startup=None, **kwargs):
    """Dive into the process from your diving point
    for debug, break, and inspection of the target
    --- Put me at breakpoint.
    
    target : object or module. Default None sets target as __main__.
       app : an instance of App.
                Default None may create a local App and the mainloop.
                If app is True, neither the app nor the mainloop will be created.
                If app is given and not started the mainloop yet,
                the app will enter the mainloop herein.
   startup : called after started up (not before)
  **kwargs : Nautilus arguments
    locals : additional context (localvars:dict) to the shell
    execStartupScript : First, execute your script ($PYTHONSTARTUP:~/.py)
    """
    quote_unqoute = """
        Anything one man can imagine, other man can make real.
        --- Jules Verne (1828--1905)
        """
    kwargs.setdefault('introText', "mwx {}".format(__version__) + quote_unqoute)
    
    app = app or wx.GetApp() or wx.App()
    frame = ShellFrame(None, target, **kwargs)
    frame.Unbind(wx.EVT_CLOSE) # EVT_CLOSE surely close the window
    frame.Show()
    frame.rootshell.SetFocus()
    if startup:
        shell = frame.rootshell
        try:
            startup(shell)
            frame.handler.bind("shell_cloned", startup)
        except Exception as e:
            shell.message("- Failed to startup: {!r}".format(e))
            traceback.print_exc()
        else:
            shell.message("The startup was completed successfully.")
    if isinstance(app, wx.App) and not app.GetMainLoop():
        app.MainLoop()
    return frame


def watchit(target=None, **kwargs):
    """Diver's watch to go deep into the wx process to inspect the target
    Wx.py tool for watching tree structure and events across the wx.Objects
    
  **kwargs : InspectionTool arguments
    pos, size, conifg, locals, and app
    """
    from wx.lib.inspection import InspectionTool
    if target:
        kwargs.update(locals=target.__dict__)
    it = InspectionTool()
    it.Init(**kwargs)
    it.Show(target)
    return it._frame


def monitor(target=None, **kwargs):
    """Wx.py tool for watching events of the target
    """
    from wx.lib.eventwatcher import EventWatcher
    ew = EventWatcher(None, **kwargs)
    ew.watch(target)
    ew.Show()
    return ew


def filling(target=None, label=None, **kwargs):
    """Wx.py tool for watching ingredients of the target
    """
    from wx.py.filling import FillingFrame
    frame = FillingFrame(rootObject=target,
                         rootLabel=label or typename(target),
                         static=False, # update each time pushed
                         **kwargs)
    frame.filling.text.WrapMode = 0 # no wrap
    frame.filling.text.Zoom = -1 # zoom level of size of fonts
    frame.Show()
    return frame


if __name__ == '__main__':
    SHELLSTARTUP = """
if 1:
    self
    self.shellframe
    self.shellframe.rootshell
    dive(self.shellframe)
    """
    print("Python {}".format(sys.version))
    print("wxPython {}".format(wx.version()))
    
    import numpy as np
    ## from scipy import constants as const
    np.set_printoptions(linewidth=256) # default 75
    
    app = wx.App()
    frm = Frame(None,
        title=repr(Frame),
        style=wx.DEFAULT_FRAME_STYLE, #&~(wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX),
        size=(200,80),
    )
    frm.editor = Editor(frm)
    
    frm.handler.debug = 0
    frm.editor.handler.debug = 0
    frm.shellframe.handler.debug = 4
    frm.shellframe.rootshell.handler.debug = 0
    frm.shellframe.Show()
    frm.shellframe.rootshell.SetFocus()
    frm.shellframe.rootshell.Execute(SHELLSTARTUP)
    frm.Show()
    app.MainLoop()
