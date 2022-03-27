#! python3
# -*- coding: utf-8 -*-
"""mwxlib param controller and wx custom controls

Author: Kazuya O'moto <komoto@jeol.co.jp>
"""
from itertools import chain
import sys
import wx
import numpy as np
from numpy import nan, inf
try:
    from utilus import SSM
    import framework as mwx
    import images
except ImportError:
    from .utilus import SSM
    from . import framework as mwx
    from . import images
import wx.lib.platebtn as pb
import wx.lib.scrolledpanel as scrolled

from six import string_types

## EPSILON = sys.float_info.epsilon
## EPSILON = 1e-15


class Param(object):
    """Standard Parameter
    
Attributes:
       name : label
      range : range [min:max:step]
    min,max : lower and upper limits
  std_value : standard value (default None)
      value : current value := std_value + offset
     offset : ditto (if std_value is None, this is the same as `value)
      knobs : knob list
      index : knob index -> reset -> callback
      check : knob tick (undefined)
        tip : doc:str also shown as a tooltip
   callback : single state machine that handles following events:
            control -> when `index changed by knobs or reset (call handler)
            check -> when `check ticks on/off (call updater)
            overflow -> when `value overflows
            underflow -> when `value underflows

Args:
        fmt : text formatter or format str (default is '%g')
              `hex` specifies hexadecimal format/eval
    handler : called when control changed
    updater : called when check changed
        tip : tooltip:str shown on the associated knobs
    """
    def __init__(self, name, range=None, value=None, fmt=None,
                 handler=None, updater=None, tip=None):
        self.__knobs = []
        self.__name = name
        self.range = range
        self.__value = value if value is not None else self.min
        self.__std_value = value
        if fmt is hex:
            self.__eval = lambda v: int(v, 16)
            self.__format = lambda v: '{:04X}'.format(int(v))
        else:
            self.__eval = lambda v: eval(v)
            self.__format = fmt if callable(fmt) else (lambda v: (fmt or "%g") % v)
        self.__check = 0
        self.__callback = SSM({
            'control' : [ handler ] if handler else [],
             'update' : [ updater ] if updater else [],
              'check' : [ updater ] if updater else [],
           'overflow' : [],
          'underflow' : [],
        })
        tip = '\n'.join(filter(None, (tip,
                                      handler and handler.__doc__,
                                      updater and updater.__doc__)))
        self.tip = tip.strip()
    
    def __str__(self, v=None):
        v = self.__value if v is None else v
        try:
            return self.__format(v)
        except ValueError:
            return str(v)
    
    def __len__(self):
        return len(self.__range)
    
    name = property(
        lambda self: self.__name,
        lambda self,v: self.set_name(v))
    
    value = property(
        lambda self: self.__value,
        lambda self,v: self.set_value(v) and self._notify())
    
    std_value = property(
        lambda self: self.__std_value,
        lambda self,v: self.set_std_value(v))
    
    offset = property(
        lambda self: self.get_offset(),
        lambda self,v: self.set_offset(v))
    
    range = property(
        lambda self: self.get_range(),
        lambda self,v: self.set_range(v))
    
    min = property(lambda self: self.__range[0])
    max = property(lambda self: self.__range[-1])
    
    index = property(
        lambda self: self.get_index(),
        lambda self,j: self.set_index(j))
    
    ## rindex = property(
    ##     lambda self: len(self) - self.get_index() - 1,
    ##     lambda self,j: self.set_index(len(self) - j - 1))
    
    knobs = property(
        lambda self: self.__knobs)
    
    check = property(
        lambda self: self.__check,
        lambda self,v: self.set_check(v))
    
    callback = property(
        lambda self: self.__callback)
    
    def bind(self, f=None, target='control'):
        la = self.__callback[target]
        if not f:
            return lambda f: self.bind(f, target)
        if f not in la:
            la.append(f)
        return f
    
    def unbind(self, f=None, target='control'):
        la = self.__callback[target]
        if not f:
            la[:] = [a for a in la if not callable(a)]
            return
        if f in la:
            la.remove(f)
    
    def reset(self, v=None, backcall=True):
        """Reset value when indexed (by knobs) with callback"""
        if v is None or v == '':
            v = self.__std_value
            if v is None:
                return
        elif v == 'nan': v = nan
        elif v == 'inf': v = inf
        elif isinstance(v, string_types):
            v = self.__eval(v.replace(',', '')) # eliminates commas(, to be deprecated)
            ## v = self.__eval(v)
        self.set_value(v)
        if backcall:
            self.__callback('control', self)
    
    def _notify(self):
        for knob in self.knobs:
            knob.notify_ctrl()
    
    def set_check(self, v):
        self.__check = v
        self.__callback('check', self)
        for knob in self.knobs:
            knob.update_label()
    
    def set_name(self, v):
        self.__name = v
        for knob in self.knobs:
            knob.update_label()
    
    def set_value(self, v):
        """Set value and check the limit.
        If the value is out of range, modify the value.
        """
        if v is None:
            v = nan
        if v in (nan, inf):
            self.__value = v
            for knob in self.knobs:
                knob.update_ctrl(None)
            return
        elif v == self.__value:
            return
        
        valid = (self.min <= v <= self.max)
        if valid:
            self.__value = v
        elif v < self.min:
            self.__value = self.min
            self.__callback('underflow', self)
        else:
            self.__value = self.max
            self.__callback('overflow', self)
        for knob in self.knobs:
            knob.update_ctrl(valid)
        return valid
    
    def set_std_value(self, v):
        self.__std_value = v
        for knob in self.knobs:
            knob.update_label()
    
    def get_offset(self):
        if self.__std_value is not None:
            return self.__value - self.__std_value
        return self.__value
    
    def set_offset(self, v):
        if self.__std_value is not None:
            if v is not nan: # Note: nan +x is not nan
                v += self.__std_value
        self.set_value(v)
    
    def get_range(self):
        return self.__range
    
    def set_range(self, v):
        if v is None:
            self.__range = [nan] # dummy data
        else:
            self.__range = sorted(v)
        for knob in self.knobs:
            knob.update_range() # list range of related knobs
    
    def get_index(self, v=None):
        if v is None:
            v = self.value
        return int(np.searchsorted(self.__range, v))
    
    def set_index(self, j):
        n = len(self)
        i = (0 if j<0 else j if j<n else -1)
        return self.set_value(self.__range[i])


class LParam(Param):
    """Linear Parameter
    """
    __doc__ = Param.__doc__
    
    min = property(lambda self: self.__min)
    max = property(lambda self: self.__max)
    step = property(lambda self: self.__step)
    
    def __len__(self):
        return 1 + self.get_index(self.max) # includes [min,max]
    
    def get_range(self):
        return np.arange(self.min, self.max + self.step, self.step)
    
    def set_range(self, v):
        if v is None:
            v = (0, 0)
        self.__min = v[0]
        self.__max = v[1]
        self.__step = v[2] if len(v) > 2 else 1
        for knob in self.knobs:
            knob.update_range() # linear range of related knobs
    
    def get_index(self, v=None):
        if v is None:
            v = self.value
        return int(round((v - self.min) / self.step))
    
    def set_index(self, j):
        return self.set_value(self.min + j * self.step)


## --------------------------------
## Knob unit for Parameter Control 
## --------------------------------

class Knob(wx.Panel):
    """Parameter controller unit
    パラメータクラスのコントロールノブ
    
    In addition to direct key input to the textctrl,
    [up][down][wheelup][wheeldown] keys can be used,
    with modifiers S- 2x, C- 16x, and M- 256x steps.
    [Mbutton] resets to the std. value if it exists.
    
Attributes:
      param : A param <Param> object referred from knobs

Args:
        par : Param <object>
       type : ctrl type (slider[*], [hv]spin, choice, and default None)
      style : style of label
              None -> static text (default)
              chkbox -> label with check box
              button -> label with flat button
   editable : textctrl is editable or readonly
   lw,tw,cw : width of label, textbox, and ctrl (default height `h=22 of widgets)
    """
    @property
    def param(self):
        return self.__par
    
    @param.setter
    def param(self, v):
        self.__par.knobs.remove(self)
        self.__par = v
        self.__par.knobs.append(self)
        self.update_range()
        self.update_ctrl()
    
    def __init__(self, parent, par, type='slider',
                 style=None, editable=1, lw=-1, tw=-1, cw=-1, h=22):
        wx.Panel.__init__(self, parent)
        self.__bit = 1
        self.__par = par
        self.__par.knobs.append(self) # パラメータの関連付けを行う
        
        if type is None:
            type = 'slider'
            cw = 0
        elif type == 'choice':
            if cw < 0:
                cw = 20
            cw += tw
            tw = 0
        
        label = self.__par.name + '  '
        
        if style == 'chkbox':
            if lw >= 0:
                lw += 16
            self.label = wx.CheckBox(self, label=label, size=(lw,-1))
            self.label.Bind(wx.EVT_CHECKBOX, self.OnCheck)
            
        elif style == 'button':
            if lw >= 0:
                lw += 16
            self.label = pb.PlateButton(self, label=label, size=(lw,-1),
                            style=(pb.PB_STYLE_DEFAULT | pb.PB_STYLE_SQUARE))
            self.label.Bind(wx.EVT_BUTTON, self.OnPress)
            
        elif not style:
            self.label = wx.StaticText(self, label=label, size=(lw,-1))
        else:
            raise Exception("unknown style: {!r}".format(style))
        
        self.label.Enable(lw)
        self.label.Bind(wx.EVT_MIDDLE_DOWN, lambda v: self.__par.reset())
        
        self.label.SetToolTip(self.__par.tip)
        
        if editable:
            self.text = wx.TextCtrl(self, size=(tw,h), style=wx.TE_PROCESS_ENTER)
            self.text.Bind(wx.EVT_TEXT, self.OnText)
            self.text.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter)
            self.text.Bind(wx.EVT_SET_FOCUS, self.OnTextFocus)
            self.text.Bind(wx.EVT_KILL_FOCUS, self.OnTextFocusKill)
            
            if type[-1] == '*':
                self.text.Bind(wx.EVT_KEY_DOWN, self.OnTextKeyDown)
            else:
                self.text.Bind(wx.EVT_KEY_DOWN, self.OnTextKey)
                self.text.Bind(wx.EVT_KEY_UP, self.OnTextKeyUp)
            
            self.text.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
            self.text.Bind(wx.EVT_MIDDLE_DOWN, lambda v: self.__par.reset())
        else:
            self.text = wx.TextCtrl(self, size=(tw,h), style=wx.TE_READONLY)
        
        self.text.Enable(tw)
        
        if type == 'slider':
            self.ctrl = wx.Slider(self, size=(cw,h), style=wx.SL_HORIZONTAL)
            self.ctrl.Bind(wx.EVT_SCROLL_CHANGED, self.OnScroll)
            self.ctrl.Bind(wx.EVT_KEY_DOWN, self.OnCtrlKeyDown)
            self.ctrl.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
            
        elif type == 'slider*':
            self.ctrl = wx.Slider(self, size=(cw,h), style=wx.SL_HORIZONTAL)
            self.ctrl.Bind(wx.EVT_SCROLL, self.OnScroll) # called while dragging
            self.ctrl.Bind(wx.EVT_SCROLL_CHANGED, lambda v: None) # pass no action
            self.ctrl.Bind(wx.EVT_KEY_DOWN, self.OnCtrlKeyDown)
            self.ctrl.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
            
        elif type == 'spin' or type =='hspin':
            self.ctrl = wx.SpinButton(self, size=(cw,h), style=wx.SP_HORIZONTAL)
            self.ctrl.Bind(wx.EVT_SPIN, self.OnScroll)
            self.ctrl.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
            
        elif type == 'vspin':
            self.ctrl = wx.SpinButton(self, size=(cw,h), style=wx.SP_VERTICAL)
            self.ctrl.Bind(wx.EVT_SPIN, self.OnScroll)
            self.ctrl.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
            
        elif type == 'choice':
            self.ctrl = wx.Choice(self, size=(cw,h))
            self.ctrl.Bind(wx.EVT_CHOICE, self.OnScroll)
            self.ctrl.SetValue = self.ctrl.SetSelection # setter of choice
            self.ctrl.GetValue = self.ctrl.GetSelection # getter (ditto)
            
        else:
            raise Exception("unknown type: {!r}".format(type))
        
        c = bool(cw)
        self.ctrl.Enable(c)
        self.ctrl.Bind(wx.EVT_MIDDLE_DOWN, lambda v: self.__par.reset())
        
        self.SetSizer(
            mwx.pack(self,
                (self.label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, lw and 1),
                (self.text,  0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, tw and 1),
                (self.ctrl,  c, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, cw and 1),
            )
        )
        self.update_range()
        self.update_ctrl()
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
    
    def OnDestroy(self, evt):
        self.__par.knobs.remove(self) # パラメータの関連付けを解除する
        evt.Skip()
    
    def update_range(self):
        v = self.__par
        if isinstance(self.ctrl, wx.Choice):
            self.ctrl.Set([v.__str__(x) for x in v.range]) #<wx.Choice>
        else:
            self.ctrl.SetRange(0, len(v)-1) #<wx.Slider> #<wx.SpinButton>
    
    def update_label(self):
        v = self.__par
        if isinstance(self.label, wx.CheckBox):
            self.label.SetValue(bool(v.check))
        
        if self.label.IsEnabled():
            t = '  ' if v.std_value is None or v.value == v.std_value else '*'
            self.label.SetLabel(v.name + t)
            self.label.Refresh()
    
    def update_ctrl(self, valid=True):
        v = self.__par
        try:
            j = v.index
        except (OverflowError, ValueError):
            ## OverflowError: cannot convert float infinity to integer
            ## ValueError: cannot convert float NaN to integer
            j = -1
        
        self.ctrl.SetValue(j)
        self.text.SetValue(str(v)) # => OnText
        if valid:
            self.set_textcolour('#ffffff') # True: white
        elif valid is None:
            self.set_textcolour('#ffff80') # None: light-yellow
        else:
            self.set_textcolour('#ff8080') # Otherwise: light-red
        self.update_label()
    
    def notify_ctrl(self):
        self.set_textcolour('#ffff80') # light-yellow
        def reset_color():
            if self:
                self.set_textcolour('white')
        wx.CallAfter(wx.CallLater, 1000, reset_color)
    
    def set_textcolour(self, c):
        try:
            if self.text.IsEditable():
                self.text.SetBackgroundColour(c)
            self.text.Refresh()
        except RuntimeError:
            ## wrapped C/C++ object of type TextCtrl has been deleted
            pass
    
    def shift(self, evt, bit, **kwargs):
        if evt.ShiftDown():   bit *= 2
        if evt.ControlDown(): bit *= 16
        if evt.AltDown():     bit *= 256
        i = self.ctrl.GetValue()
        self.__par.index = i + int(bit)
        self.__par.reset(self.__par.value, **kwargs)
    
    def OnScroll(self, evt): #<wx._core.ScrollEvent><wx._controls.SpinEvent><wx._core.CommandEvent>
        self.__par.index = self.ctrl.GetValue()
        self.__par.reset(self.__par.value)
        evt.Skip()
    
    def OnMouseWheel(self, evt): #<wx._core.MouseEvent>
        self.shift(evt, 1 if evt.WheelRotation>0 else -1)
        evt.Skip(False)
    
    def OnCtrlKeyDown(self, evt): #<wx._core.KeyEvent>
        key = evt.GetKeyCode()
        if key == wx.WXK_LEFT: return self.shift(evt, -1)
        if key == wx.WXK_RIGHT: return self.shift(evt, 1)
        
        def focus(c):
            if isinstance(c, Knob) and c.ctrl.IsEnabled():
                c.ctrl.SetFocus()
                return True
        
        ls = next(x for x in self.Parent.layout_groups if self in x)
        i = ls.index(self)
        if key == wx.WXK_DOWN: return any(focus(c) for c in ls[i+1:])
        if key == wx.WXK_UP: return any(focus(c) for c in ls[i-1::-1])
    
    def OnTextKey(self, evt): #<wx._core.KeyEvent>
        key = evt.GetKeyCode()
        if key == wx.WXK_DOWN: return self.shift(evt, -1, backcall=None)
        if key == wx.WXK_UP: return self.shift(evt, 1, backcall=None)
        evt.Skip()
    
    def OnTextKeyUp(self, evt): #<wx._core.KeyEvent>
        key = evt.GetKeyCode()
        if key == wx.WXK_DOWN: return self.shift(evt, 0) # only up/down updates (bit=0)
        if key == wx.WXK_UP: return self.shift(evt, 0)
        evt.Skip()
    
    def OnTextKeyDown(self, evt): #<wx._core.KeyEvent>
        key = evt.GetKeyCode()
        if key == wx.WXK_DOWN: return self.shift(evt, -1)
        if key == wx.WXK_UP: return self.shift(evt, 1)
        if key == wx.WXK_ESCAPE:
            self.__par.reset(self.__par.value, backcall=None) # restore value
        evt.Skip()
    
    def OnText(self, evt): #<wx._core.CommandEvent>
        evt.Skip()
        x = self.text.Value.strip()
        if x != str(self.__par):
            self.set_textcolour('#ffff80') # light-yellow
        else:
            self.set_textcolour('white')
    
    def OnTextEnter(self, evt): #<wx._core.CommandEvent>
        evt.Skip()
        x = self.text.Value.strip()
        self.__par.reset(x)
    
    def OnTextFocus(self, evt): #<wx._core.FocusEvent>
        evt.Skip()
    
    def OnTextFocusKill(self, evt): #<wx._core.FocusEvent>
        if self.__par.value in (nan, inf):
            evt.Skip()
            return
        x = self.text.Value.strip()
        if x != str(self.__par):
            try:
                self.__par.reset(x) # update value if focus out
            except Exception:
                self.text.SetValue(str(self.__par))
                self.__par.reset(self.__par.value, backcall=None) # restore value
        else:
            self.text.SetValue(x)
            self.set_textcolour('white')
        evt.Skip()
    
    def OnCheck(self, evt): #<wx._core.CommandEvent>
        self.__par.check = int(evt.IsChecked())
        evt.Skip()
    
    def OnPress(self, evt): #<wx._core.CommandEvent>
        ## self.__par.check = True
        self.__par.callback('update', self.__par)
        evt.Skip()
    
    def Enable(self, p=True):
        self.label.Enable(p)
        self.ctrl.Enable(p)
        self.text.Enable(p)


class ControlPanel(scrolled.ScrolledPanel):
    """Scrollable Control Panel
    スクロール可能なコントロール配置用パネル
    """
    def __init__(self, *args, **kwargs):
        scrolled.ScrolledPanel.__init__(self, *args, **kwargs)
        
        self.SetSizer(mwx.pack(self, orient=wx.VERTICAL))
        self.SetupScrolling()
        
        self.__groups = []
        self.__params = []
        
        self.Menu = [
            (wx.ID_COPY, "&Copy params", "Copy params",
                lambda v: self.copy_to_clipboard(),
                lambda v: v.Enable(self.__params != [])),
                
            (wx.ID_PASTE, "&Paste params", "Read params",
                lambda v: self.paste_from_clipboard(),
                lambda v: v.Enable(self.__params != [])),
            (),
            (wx.ID_RESET, "&Reset params", "Reset params",
                lambda v: self.reset_params(),
                lambda v: v.Enable(self.__params != [])),
        ]
        self.Bind(wx.EVT_CONTEXT_MENU, lambda v: mwx.Menu.Popup(self, self.Menu))
        self.Bind(wx.EVT_LEFT_DOWN, self.OnToggleFold)
        
        self.Bind(wx.EVT_SCROLLWIN_THUMBRELEASE, self.OnRecalcLayout)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnRecalcLayout)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnRecalcLayout)
    
    def OnRecalcLayout(self, evt): #<wx._core.ScrollWinEvent>
        self.Layout()
        evt.Skip()
    
    def OnToggleFold(self, evt): #<wx._core.MouseEvent>
        x, y = evt.Position
        for child in self.Sizer.Children: # child <wx._core.SizerItem>
            if child.IsShown():
                obj = child.Sizer or child.Window
                if isinstance(obj, (wx.StaticBoxSizer, wx.StaticBox)):
                    cx, cy = obj.Position
                    if cx < x < cx + obj.Size[0] and cy < y < cy+22:
                        for cc in obj.Children: # child of child <wx._core.SizerItem>
                            cc.Show(not cc.IsShown())
                        self.Layout()
                        self.SendSizeEvent()
                        break
        evt.Skip()
    
    def Scroll(self, *args):
        """Scrolls a window so the view start is at the given point.
        (override) to aviod DeprecationWarning: an integer is required.
        """
        if len(args) == 1:
            args = args[0]
        x, y = [int(v) for v in args]
        return scrolled.ScrolledPanel.Scroll(self, x, y)
    
    ## --------------------------------
    ## Layout commands and attributes
    ## --------------------------------
    @property
    def layout_groups(self):
        return self.__groups
    
    def is_enabled(self, groupid, pred=all):
        return pred(win.Enabled for win in self.__groups[groupid])
    
    def enable(self, groupid, p=True):
        for win in self.__groups[groupid]: # child could be deep nesting
            win.Enable(p)
    
    def is_shown(self, groupid):
        ## child = self.Sizer.Children[groupid]
        ## return child.IsShown()
        return self.Sizer.IsShown(groupid % len(self.__groups))
    
    def show(self, groupid, p=True):
        """show/hide all including the box"""
        ## child = self.Sizer.Children[groupid]
        ## child.Show(p)
        self.Sizer.Show(groupid % len(self.__groups), p)
        ## self.Sizer.Fit(self) # do Fit(self.Parent) if needed
        self.Layout()
        self.Parent.SendSizeEvent() # let parent redraw the child panel
    
    def is_folded(self, groupid):
        child = self.Sizer.Children[groupid]
        return not any(cc.IsShown() for cc in child.Sizer.Children)
    
    def fold(self, groupid, p=True):
        """fold/unfold the boxed group"""
        child = self.Sizer.Children[groupid]
        if isinstance(child.Sizer, wx.StaticBoxSizer) and child.IsShown():
            for cc in child.Sizer.Children: # child of child <wx._core.SizerItem>
                cc.Show(not p)
            ## self.Sizer.Fit(self) # do Fit(self.Parent) if needed
            self.Layout()
            self.Parent.SendSizeEvent() # let parent redraw the child panel
    
    def layout(self, objs, title=None,
               row=1, expand=0, border=2, hspacing=1, vspacing=1,
               show=True, visible=True, fix=True, align=wx.ALIGN_LEFT,
               **kwargs):
        """Do layout (cf. Layout) using mwx.pack
        
        title : box header string (default is None - no box)
         objs : list of Params, wx.Objects, tuple of sizing, or None
          row : number of row to arange widgets
         show : fold or unfold the boxed group
       expand : (0) fixed size
                (1) to expand horizontally
                (2) to exapnd horizontally and vertically
       border : size of outline border
  [hv]spacing : spacing among packed objs inside the group
        align : alignment flag (wx.ALIGN_*) default is ALIGN_LEFT
          fix : tell sizer to fix the minimum layout
     **kwargs : extra keyword arguments given for Knob
        """
        ## assert all((key in inspect.getargspec(Knob)[0]) for key in kwargs)
        assert not isinstance(objs, string_types)
        
        objs = [ (c, 0, wx.EXPAND) if isinstance(c, wx.StatusBar)
            else (c, 1, wx.EXPAND | wx.ALL, 1) if isinstance(c, wx.StaticLine)
            else c if c is None
            else c if isinstance(c, tuple)
            else c if isinstance(c, wx.Object)
            else Knob(self, c, **kwargs) for c in objs ]
        
        def flatten(a):
            for y in a:
                for x in (flatten(y) if isinstance(y, tuple) else (y,)):
                    yield x
        
        self.__groups.append(list(c for c in flatten(objs)
                                          if isinstance(c, wx.Object)))
        
        def var(c):
            if isinstance(c, Knob):
                return c.param
            elif hasattr(c, 'value'):
                return c
        
        self.__params.append(list(filter(None, (var(c) for c in objs))))
        
        ## do layout in row
        p = wx.EXPAND if expand > 0 else wx.ALIGN_CENTER
        if row > 1:
            objs = [mwx.pack(self, *objs[i:i+row], orient=wx.HORIZONTAL,
                        style=(expand>0, p | wx.LEFT | wx.RIGHT, hspacing))
                            for i in range(0, len(objs), row)]
        
        p = wx.EXPAND if expand > 0 else align
        sizer = mwx.pack(self, *objs, label=title, orient=wx.VERTICAL,
                    style=(expand>1, p | wx.BOTTOM | wx.TOP, vspacing))
        
        self.Sizer.Add(sizer, expand>1, p | wx.ALL, border)
        self.show(-1, visible)
        self.fold(-1, not show)
        if fix:
            self.Sizer.Fit(self)
    
    ## --------------------------------
    ## 外部入出力／クリップボード通信
    ## --------------------------------
    @property
    def parameters(self):
        return [p.value for p in chain(*self.__params)]
    
    @parameters.setter
    def parameters(self, v):
        self.reset_params(v)
    
    def get_params(self, checked_only=False):
        params = chain(*self.__params)
        if not checked_only:
            return params
        return filter(lambda c: getattr(c, 'check', None), params)
    
    def reset_params(self, argv=None, checked_only=False, **kwargs):
        params = self.get_params(checked_only)
        if not argv:
            for p in params:
                try:
                    p.reset(**kwargs)
                except AttributeError:
                    pass
        else:
            for p,v in zip(params, argv):
                try:
                    p.reset(v, **kwargs) # eval v:str -> value
                except AttributeError:
                    p.value = v
                except Exception as e: # failed to eval
                    print("- Failed to reset {!r}: {}".format(p, e))
                    pass
    
    def copy_to_clipboard(self, checked_only=False):
        params = self.get_params(checked_only)
        text = '\t'.join(str(p) if isinstance(p, Param)
                         else str(p.value) for p in params)
        Clipboard.write(text)
    
    def paste_from_clipboard(self, checked_only=False, **kwargs):
        text = Clipboard.read()
        self.reset_params(text.split('\t'), checked_only, **kwargs)


class Clipboard:
    """Clipboard interface of text
    
    This does not work unless wx.App instance exists.
    The clipboard data cannot be transferred unless wx.Frame exists.
    """
    verbose = True
    
    @staticmethod
    def read():
        do = wx.TextDataObject()
        wx.TheClipboard.Open() or print("- Unable to open the clipboard")
        wx.TheClipboard.GetData(do)
        wx.TheClipboard.Close()
        text = do.GetText()
        if Clipboard.verbose:
            print("From clipboard: {}".format(text))
        return text
    
    @staticmethod
    def write(text):
        do = wx.TextDataObject(str(text))
        wx.TheClipboard.Open() or print("- Unable to open the clipboard")
        wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()
        if Clipboard.verbose:
            print("To clipboard: {}".format(text))


## --------------------------------
## Wx custom controls and bitmaps 
## --------------------------------
if 1:
    provided_arts = {
            'cut' : wx.ART_CUT,
           'copy' : wx.ART_COPY,
          'paste' : wx.ART_PASTE,
           'book' : wx.ART_HELP_BOOK,
           'page' : wx.ART_HELP_PAGE,
            'exe' : wx.ART_EXECUTABLE_FILE,
           'file' : wx.ART_NORMAL_FILE,
       'file_new' : wx.ART_NEW,
    'file_delete' : wx.ART_DELETE,
   'file_missing' : wx.ART_MISSING_IMAGE,
           'find' : wx.ART_FIND,
           'open' : wx.ART_FILE_OPEN,
           'save' : wx.ART_FILE_SAVE,
         'saveas' : wx.ART_FILE_SAVE_AS,
         'folder' : wx.ART_FOLDER,
    'folder_open' : wx.ART_FOLDER_OPEN,
             #'x' : wx.ART_CLOSE,
             #'v' : wx.ART_TICK_MARK,
              '?' : wx.ART_QUESTION,
              '!' : wx.ART_INFORMATION,
             '!!' : wx.ART_WARNING,
            '!!!' : wx.ART_ERROR,
              '+' : wx.ART_PLUS,
              '-' : wx.ART_MINUS,
              '~' : wx.ART_GO_HOME,
             'up' : wx.ART_GO_UP,
             'dn' : wx.ART_GO_DOWN,
             '<-' : wx.ART_GO_BACK,
             '->' : wx.ART_GO_FORWARD,
            '|<-' : wx.ART_GOTO_FIRST,
            '->|' : wx.ART_GOTO_LAST,
    }

def Icon(key, size=None):
    if key:
        try:
            art = getattr(images, key)
            if not size:
                bmp = art.GetBitmap()
            else:
                bmp = (art.GetImage()
                          .Scale(*size, wx.IMAGE_QUALITY_NEAREST)
                          .ConvertToBitmap())
        except Exception:
            bmp = wx.ArtProvider.GetBitmap(
                    provided_arts.get(key) or key,
                    size=size or (16,16))
        return bmp
    
    ## Note: null (0-shaped) bitmap fails with AssertionError from 4.1.0
    if key == '':
        bmp = wx.Bitmap(size or (16,16))
        if 1:
            dc = wx.MemoryDC(bmp)
            dc.SetBackground(wx.Brush('black'))
            dc.Clear()
            del dc
        bmp.SetMaskColour('black') # return dummy-sized blank bitmap
        return bmp
    return wx.NullBitmap # The standard wx controls accept this,

Icon.provided_arts = provided_arts

Icon.custom_images = dict((k,v) for (k,v) in images.__dict__.items()
                          if isinstance(v, wx.lib.embeddedimage.PyEmbeddedImage))


def _bmpIcon(v):
    if isinstance(v, string_types):
        return Icon(v)
    return v


class Button(pb.PlateButton):
    """Flat button
    
Attributes:
       icon : key:str for Icon

Args:
      label : button label
    handler : event handler when the button is pressed
       icon : key:str for button icon
        tip : tip:str displayed on the button
   **kwargs : keywords for wx.lib.platebtn.PlateButton
    """
    @property
    def icon(self):
        return self.__icon
    
    @icon.setter
    def icon(self, v):
        self.__icon = v
        self.SetBitmap(_bmpIcon(v))
        self.Refresh()
    
    def __init__(self, parent, label='',
                 handler=None, icon=None, tip='', **kwargs):
        kwargs.setdefault('style', pb.PB_STYLE_DEFAULT | pb.PB_STYLE_SQUARE)
        pb.PlateButton.__init__(self, parent, -1, label, **kwargs)
        
        if handler:
            self.Bind(wx.EVT_BUTTON, handler)
        
        tip = '\n  '.join(filter(None, (tip, handler and handler.__doc__)))
        self.ToolTip = tip.strip()
        self.icon = icon
    
    def SetBitmap(self, bmp):
        """Set the bitmap displayed in the button
        (override) If it fails, it clears the bitmap.
        """
        try:
            pb.PlateButton.SetBitmap(self, bmp)
        except Exception:
            self._bmp = dict(enable=None, disable=None)


class ToggleButton(wx.ToggleButton):
    """Togglable button
    
Attributes:
       icon : key:str for Icon

Args:
      label : button label
    handler : event handler when the button is pressed
       icon : key:str for button icon
        tip : tip:str displayed on the button
   **kwargs : keywords for wx.ToggleButton

Note:
    To get the status, check Value or event.GetInt or event.IsChecked.
    """
    @property
    def icon(self):
        return self.__icon
    
    @icon.setter
    def icon(self, v):
        self.__icon = v
        if isinstance(v, tuple):
            v, w = v
            self.SetBitmapPressed(_bmpIcon(w))
        if v:
            self.SetBitmap(_bmpIcon(v))
        self.Refresh()
    
    def __init__(self, parent, label='',
                 handler=None, icon=None, tip='', **kwargs):
        wx.ToggleButton.__init__(self, parent, -1, label, **kwargs)
        
        if handler:
            self.Bind(wx.EVT_TOGGLEBUTTON, handler)
        
        tip = '\n  '.join(filter(None, (tip, handler and handler.__doc__)))
        self.ToolTip = tip.strip()
        self.icon = icon


class TextCtrl(wx.Panel):
    """Text panel
    
Attributes:
      Value : textctrl value:str
       icon : Icon key:str

Args:
      label : button label
    handler : event handler when text is entered
    updater : event handler when the button is pressed
       icon : key:str for button icon
        tip : tip:str displayed on the button
   readonly : flag:bool for wx.TE_READONLY
   **kwargs : keywords for wx.TextCtrl
        e.g., value:str
    """
    Value = property(
        lambda self: self.ctrl.GetValue(),
        lambda self,v: self.ctrl.SetValue(v))
    
    value = Value # internal use only
    
    @property
    def icon(self):
        return self.btn.icon
    
    @icon.setter
    def icon(self, v):
        self.btn.icon = v
    
    def __init__(self, parent, label='', handler=None, updater=None,
                 icon=None, tip='', readonly=0, **kwargs):
        wx.Panel.__init__(self, parent, size=kwargs.get('size') or (-1,22))
        
        self.btn = Button(self, label, icon=icon, tip=tip,
                          size=(-1,-1) if label or icon else (0,0))
        
        kwargs['style'] = (kwargs.get('style', 0)
                            | wx.TE_PROCESS_ENTER
                            | (wx.TE_READONLY if readonly else 0))
        
        self.ctrl = wx.TextCtrl(self, **kwargs)
        ## self.ctrl.Hint = hint
        
        self.SetSizer(
            mwx.pack(self,
                (self.btn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 0),
                (self.ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 0),
            )
        )
        if handler:
            ## use style=wx.TE_PROCESS_ENTER
            self.ctrl.Bind(wx.EVT_TEXT_ENTER, lambda v: handler(self))
        if updater:
            self.btn.Bind(wx.EVT_BUTTON, lambda v: updater(self))


class Choice(wx.Panel):
    """Editable Choice (ComboBox) panel
    
Attributes:
  Selection : combobox selection:int
      Value : combobox value:str
       icon : Icon key:str

Args:
      label : button label
    handler : event handler when text is entered or item is selected
    updater : event handler when the button is pressed
       icon : key:str for button icon
        tip : tip:str displayed on the button
   readonly : flag:bool for wx.TE_READONLY
  selection : initial selection:int for combobox
   **kwargs : keywords for wx.TextCtrl
        e.g., choices:list

Note:
    If the input item is not found in the choices,
    it will be added to the list (unless readonly)
    """
    Selection = property(
        lambda self: self.ctrl.GetSelection(),
        lambda self,v: self.ctrl.SetSelection(v))
    
    Value = property(
        lambda self: self.ctrl.GetValue(),
        lambda self,v: self.ctrl.SetValue(v))
    
    value = Value # internal use only
    
    @property
    def icon(self):
        return self.btn.icon
    
    @icon.setter
    def icon(self, v):
        self.btn.icon = v
    
    def __init__(self, parent, label='',
                 handler=None, updater=None,
                 icon=None, tip='', readonly=0, selection=None, **kwargs):
        wx.Panel.__init__(self, parent, size=kwargs.get('size') or (-1,22))
        
        self.btn = Button(self, label, icon=icon, tip=tip,
                          size=(-1,-1) if label or icon else (0,0))
        
        kwargs['style'] = (kwargs.get('style', 0)
                            | wx.TE_PROCESS_ENTER
                            | (wx.CB_READONLY if readonly else 0))
        
        self.ctrl = wx.ComboBox(self, **kwargs)
        ## self.ctrl.Hint = hint
        
        self.SetSizer(
            mwx.pack(self,
                (self.btn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 0),
                (self.ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 0),
            )
        )
        if handler:
            ## use style=wx.TE_PROCESS_ENTER
            self.ctrl.Bind(wx.EVT_TEXT_ENTER, lambda v: handler(self))
            self.ctrl.Bind(wx.EVT_COMBOBOX, lambda v: handler(self))
        self.ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)
        if updater:
            self.btn.Bind(wx.EVT_BUTTON, lambda v: updater(self))
        
        if selection is not None:
            self.ctrl.Selection = selection # no events?
    
    def OnEnter(self, evt):
        s = evt.String.strip()
        if not s:
            self.ctrl.SetSelection(-1)
        elif s not in self.ctrl.Items:
            self.ctrl.Append(s)
            self.ctrl.SetStringSelection(s)
        evt.Skip()


class Indicator(wx.Panel):
    """Traffic light indicator tricolor mode
    """
    @property
    def Value(self):
        return self.__value
    
    @Value.setter
    def Value(self, v):
        self.__value = int(v)
        self.Refresh()
    
    tricolor = ('red','yellow','green')
    spacing = 7
    radius = 5
    
    def __init__(self, parent, value=0, tip='', size=(-1,-1), **kwargs):
        s = self.spacing
        size = np.maximum((s*6, s*2+1), size) # set minimum size:(6s,2s)
        wx.Panel.__init__(self, parent, size=size, **kwargs)
        
        self.__value = value
        self.ToolTip = tip.strip()
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        N = len(self.tricolor)
        s = self.spacing
        r = self.radius
        w, h = self.ClientSize
        dc.SetBrush(wx.Brush("black"))
        dc.DrawRoundedRectangle(0, h//2-s, s*2*N-1, s*2+1, s)
        for j,name in enumerate(self.tricolor):
            if not self.__value & (1 << N-1-j):
                name = 'gray'
            dc.SetBrush(wx.Brush(name))
            dc.DrawCircle(s*(2*j+1)-j, h//2, r)


class Gauge(wx.Panel):
    """Rainbow gauge panel
    """
    @property
    def Value(self):
        return self.__value
    
    @Value.setter
    def Value(self, v):
        self.__value = int(v)
        self.Draw()
    
    @property
    def Range(self):
        return self.__range
    
    @Range.setter
    def Range(self, v):
        self.__range = int(v)
        self.Draw()
    
    def __init__(self, parent, range=24, value=0, tip='', **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.__range = range
        self.__value = value
        self.ToolTip = tip.strip()
        self.canvas = wx.Bitmap(self.ClientSize)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnSize(self, evt):
        if all(self.ClientSize):
            self.canvas = wx.Bitmap(self.ClientSize)
            self.Draw()
    
    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self, self.canvas)
    
    def Draw(self):
        dc = wx.BufferedDC(wx.ClientDC(self), self.canvas)
        dc.Clear()
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        def color(x):
            y = 4*x
            if   x < 0.25: rgb = (0, y, 1)
            elif x < 0.50: rgb = (0, 1, 2-y)
            elif x < 0.75: rgb = (y-2, 1, 0)
            else:          rgb = (1, 4-y, 0)
            return [int(round(255 * x)) for x in rgb]
        
        w, h = self.ClientSize
        N = self.__range
        for i in range(N):
            if i < self.__value:
                dc.SetBrush(wx.Brush(wx.Colour(color(i/N))))
            else:
                dc.SetBrush(wx.Brush('white'))
            dc.DrawRectangle(i*w//N, 0, w//N-1, h)


if __name__ == '__main__':
    print("Python {}".format(sys.version))
    print("wxPython {}".format(wx.version()))
    
    from numpy import pi
    
    class TestPanel(ControlPanel, mwx.CtrlInterface):
        def __init__(self, *args, **kwargs):
            ControlPanel.__init__(self, *args, **kwargs)
            mwx.CtrlInterface.__init__(self)
            
            self.handler.debug = 6
            
            a = Param('test')
            b = LParam('test')
            self.layout((a,b,))
            
            self.A =  Param('HHH', np.arange(-1, 1, 1e-3), 0.5, tip='amplitude')
            self.K = LParam('k', (0, 1, 1e-3))
            self.P = LParam('φ', (-pi, pi, pi/100), 0)
            self.Q = LParam('universe', (1, 20, 1), inf, handler=print, updater=print)
            self.R = LParam('lens', (0, 0xffff), 0x8000, handler=print, updater=print, fmt=hex)
            self.params = (
                self.A,
                self.K,
                self.P,
                self.Q,
                self.R,
            )
            for lp in self.params:
                lp.callback.update({
                    'control' : [lambda p: print("control", p.name, p.value)],
                      'check' : [lambda p: print("check", p.check)],
                   'overflow' : [lambda p: print("overflow", p)],
                  'underflow' : [lambda p: print("underflow", p)],
                })
            
            @self.K.bind
            @self.A.bind
            def p(item):
                print(item)
            
            self.layout(
                self.params, title="V1",
                row=1, expand=0, hspacing=1, vspacing=1, show=1, visible=1,
                type='slider', style='chkbox', lw=-1, tw=-1, cw=-1, h=22, editable=1
            )
            self.layout(
                self.params, title="V2",
                row=2, expand=1, hspacing=1, vspacing=2, show=1, visible=1,
                type='spin', style='button', lw=-1, tw=60, cw=-1, editable=0,
            )
            ## self.layout((
            ##     Knob(self, self.A, type, lw=32, tw=60, cw=-1, h=20)
            ##         for type in (
            ##             'vspin',
            ##             'hspin',
            ##             'choice',
            ##             'slider',
            ##             )
            ##     ),
            ##     row=2, expand=0, hspacing=1, vspacing=2, show=0, visible=1,
            ## )
    
    app = wx.App()
    frm = mwx.Frame(None)
    frm.panel = TestPanel(frm)
    frm.Fit()
    frm.Show()
    frm.SetFocus()
    app.MainLoop()
