#! python3
# -*- coding: utf-8 -*-
"""Gnuplot wrapper for py3k

Author: Kazuya O'moto <komoto@jeol.co.jp>
"""
import subprocess
import warnings
import tempfile
import sys
import os
import wx
try:
    import framework as mwx
    from controls import ControlPanel
except:
    from . import framework as mwx
    from .controls import ControlPanel
import numpy as np
from six.moves import input
from six import string_types


class Gplot(object):
    """Gnuplot - pgnuplot wrapper
    
    default markers
    std_marker : 1,2,3,
   open_marker : 4,6,8,10,12,14,
  solid_marker : 5,7,9,11,13,15,
    """
    debug = 0
    startupfile = None
    tempfile = tempfile.mktemp()
    data_format = "{:e}".format
    
    @staticmethod
    def init_path(path):
        if not os.path.isdir(path):
            print("Gplot warning: {!r} is not a directory.".format(path))
        os.environ['PATH'] = ';'.join((path, os.environ['PATH']))
    
    def __init__(self, startup="__init__.plt", debug=0):
        self.__gnuplot = subprocess.Popen(['pgnuplot'],
                            shell=True, stdin=subprocess.PIPE)
        print("Launching new gnuplot...")
        self.startupfile = startup or ""
        self.debug = debug
        self.reset()
    
    def __del__(self):
        print("bye gnuplot...")
        self.terminate()
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)
    
    def __call__(self, text):
        for t in text.splitlines():
            cmd = t.strip()
            if cmd:
                self.__gnuplot.stdin.write((cmd + '\n').encode())
                if self.debug:
                    print("pgnupot>", cmd)
        self.__gnuplot.stdin.flush()
        return self
    
    def plot(self, *args):
        if isinstance(args[0], string_types): # text command
            pcmd = [v.strip() for v in args]
            if pcmd[-1].endswith(','):
                pcmd[-1] = pcmd[-1][:-1]
            
        ## multiplot with args = (x1, y1[,opt]), (x2, y2[,opt]), ...
        elif all((type(x) is tuple) for x in args):
            pcmd = []
            with open(self.tempfile, 'w') as o:
                for i,arg in enumerate(args):
                    data = arg[:2]
                    opt = arg[2] if len(arg) > 2 else "w l"
                    for v in zip(*data):
                        o.write('\t'.join(self.data_format(x) for x in v) + '\n')
                    o.write('\n\n')
                    pcmd.append("temp index {}:{} {}".format(i, i, opt))
            
        ## plot with args = (axis, y1[,opt], y2[,opt], ...)
        else:
            axis, args = args[0], args[1:]
            data, opts = [], []
            for v in args:
                if not isinstance(v, string_types):
                    data.append(v)
                    if len(data) - len(opts) > 1: # opts 指定が省略されたのでデフォルト指定
                        opts.append("w l")
                else:
                    opts.append(v)
                    
            while len(data) > len(opts): # opts 指定の数が足りない場合 (maybe+1)
                opts.append("w l")
            
            pcmd = ["temp using 1:{} {}".format(j+2,opt) for j,opt in enumerate(opts)]
            data = np.vstack((axis, data))
            with open(self.tempfile, 'w') as o:
                for v in data.T:
                    o.write('\t'.join(self.data_format(x) for x in v) + '\n')
            
        ## self("temp = '{}'".format(self.tempfile))
        self("plot " + ', '.join(pcmd))
    
    def terminate(self):
        if self.__gnuplot is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                try:
                    self('q')
                    ## self.__gnuplot.kill()
                except Exception:
                    pass
                self.__gnuplot = None
    
    def restart(self):
        self.terminate()
        self.__init__(self.startupfile)
    
    def reset(self, startup=None):
        self("""reset
        set zeroaxis lt 9
        set grid xtics mxtics lt 13, lt 0
        set grid ytics mytics lt 13, lt 0
        set grid x2tics mx2tics lt 13, lt 0
        set grid y2tics my2tics lt 13, lt 0
        """)
        if startup is not None:
            self.startupfile = startup # startupfile を変更する
        
        if self.startupfile:
            self("load '{}'".format(self.startupfile))
        self("temp = '{}'".format(self.tempfile))
    
    def wait(self, msg=""):
        input(msg + " (Press ENTER to continue)")
    
    def pause(self, dur=-1, msg=""):
        self("pause {} '{}'".format(dur, msg))
    
    def edit(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            subprocess.Popen("notepad {}".format(self.startupfile))


## if __name__ == "__main__":
if 0:
    from numpy import pi,sin,cos
    
    Gplot.init_path("C:/usr/home/bin/gnuplot-4.4/binary")
    
    gp = Gplot(None, debug=1)
    gp("""
    ## set termoption dashed
    set termoption enhanced
    set size ratio -1
    set title 'test plot'
    set ylabel 'arb unit'
    set xtics 1.0
    set ytics 1.0
    set mxtics 5
    set mytics 5
    set xrange [-4:4]
    set yrange [-2:2]
    """)
    X = np.arange(0,2,0.1) * pi
    
    print("\n>>> 数式のプロット 1")
    gp.plot(X, sin(X), "title 'sin' w lp")
    gp.wait()
    
    print("\n>>> 数式のプロット 2")
    gp.plot((X, sin(X), "title 'sin' w lp"),
            (X/2, cos(X), "title 'cos' w lp lt 2 ps 0.5"),
            (cos(X), sin(X), "title 'circ' w lp lt 5 ps 0.5"),
    )
    gp.wait()
    
    print("\n>>> 数式のプロット 3")
    gp.plot(X, sin(X), "title 'sin' w lp",
               cos(X), "title 'cos' w lp lt 5 ps 0.5",
               np.sqrt(X),
    )
    gp.wait()
    
    print("\n>>> ファイル出力＋プロット")
    data = np.vstack((X, sin(X), cos(X)))
    ## np.savetxt(gp.tempfile, data.T, fmt='%f')
    
    with open(gp.tempfile, 'w') as o:
        for v in data.T:
            print('\t'.join("{:g}".format(x) for x in v), file=o)
            
    gp("f = '{}'".format(o.name))
    gp.plot(
        "f using 1:2 w lp",
        "f using 1:3 w lp",
    )
    gp.wait()


class GplotFrame(mwx.Frame):
    """gnuplot プロット専用のフレーム
    
    gnuplot : single class object
    """
    ## gnuplot = None
    gnuplot = property(lambda self: self.__gplot)
    
    def __init__(self, *args, **kwargs):
        mwx.Frame.__init__(self, *args, **kwargs)
        
        self.__gplot = Gplot()
        self.panel = ControlPanel(self)
        
        self.menubar["Edit"] = [
            (wx.ID_COPY, "&Copy params\tCtrl-c", "Copy params to clipboard",
                lambda v: self.panel.copy_to_clipboard()),
                
            (wx.ID_PASTE, "&Paste params\tCtrl-v", "Read params from clipboard",
                lambda v: self.panel.paste_from_clipboard()),
            (),
            (wx.ID_RESET, "&Reset params\tCtrl-n", "Reset params to ini-value",
                lambda v: self.panel.reset_params()),
        ]
        self.menubar["Gnuplot"] = [
            (mwx.ID_(80), "&Gnuplot setting\tCtrl-g", "Edit settings",
                lambda v: self.__gplot.edit(),
                lambda v: v.Enable(self.__gplot is not None)),
                
            (mwx.ID_(81), "&Reset gnuplot\tCtrl-r", "Reset setting",
                lambda v: (self.__gplot.reset(),
                           self.__gplot("replot")),
                lambda v: v.Enable(self.__gplot is not None)),
            (),
            (mwx.ID_(82), "Restart gnuplot", "Restart process",
                lambda v: (self.__gplot.restart(),
                           self.__gplot("replot")),
                lambda v: v.Enable(self.__gplot is not None)),
        ]
        self.menubar.reset()
    
    def Destroy(self):
        del self.__gplot
        return mwx.Frame.Destroy(self)


if __name__ == "__main__":
    print("Python {}".format(sys.version))
    print("wxPython {}".format(wx.version()))
    
    from numpy import pi
    from mwx.controls import LParam
    
    class TestFrame(GplotFrame):
        def __init__(self, *args, **kwargs):
            GplotFrame.__init__(self, *args, **kwargs)
            
            self.params = (
                LParam('Amp', (-1, 1, 1e-3), 0, "%8.3e"),
                LParam('k',   (0, 2, 1./100), 1, "%g"),
                LParam('φ',  (-pi, pi, pi/100), 0, "%G"),
            )
            for lp in self.params:
                lp.bind(self.plot)
            
            self.panel.layout(self.params,
                row=1, expand=1, type='slider', cw=-1, lw=32)
            
        def plot(self, par):
            a, k, p = [x.value for x in self.params]
            try:
                self.gnuplot("plot [:] [-1:1] "
                             "{:f} * sin({:f} * (x - {:f}))".format(a,k,p))
            except Exception as e:
                print(e)
                self.statusbar.write("gnuplot fail, try to restart.")
                self.gnuplot.restart()
    
    app = wx.App()
    frm = TestFrame(None)
    frm.Fit()
    frm.Show()
    frm.SetFocus()
    app.MainLoop()
