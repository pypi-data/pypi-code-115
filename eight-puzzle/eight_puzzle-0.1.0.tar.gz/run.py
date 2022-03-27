from cProfile import label
from tkinter import Frame, Label
from turtle import width
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

root = ttk.Window(title="8-puzzle",
                  themename="superhero", size=(300, 200), resizable=(0, 0))
bwidth=10
b1 = ttk.Button(root, text="Generate", bootstyle="info-outline",width=bwidth)
b1.grid(row=1, column=1, padx=(0, 50))
b2 = ttk.Button(root, text="Run", bootstyle="info-outline",width=bwidth)
b2.grid(row=1, column=2)


frame = ttk.Frame(bootstyle="secondary", borderwidth=1)
for i in range(1, 4):
    for j in range(1, 4):
        ttk.Button(frame, text=j+(i-1)*3, width=1,
                   bootstyle="info-outline").grid(row=i, column=j)
frame.grid(row=2, column=1,padx=(0, 50), pady=(20,0))

frame2 = ttk.Frame(bootstyle="secondary", borderwidth=1)
for i in range(1, 4):
    for j in range(1, 4):
        ttk.Button(frame2, text=j+(i-1)*3, width=1,
                   bootstyle="info-outline").grid(row=i, column=j)
frame2.grid(row=2, column=2, padx=0, pady=(20,0))

label=ttk.Label(text="now",bootstyle="info-reverse")
label.grid(row=3, column=1,padx=(0, 50))
label=ttk.Label(text="target",bootstyle="info")
label.grid(row=3, column=2)

root.mainloop()
