from affogato.model import Model 
from tkinter import *
import tkinter as tk
import win32gui
from PIL import ImageGrab, Image
import numpy as np
import pickle as pk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
MODEL_PATH = "model_mnist2.pickle"

def predict_image_sample(data, model, window):
    """
    shows an image and gives it to the model for prediction
    """
    plt.close(plt.gcf())
    plt.style.use('default')
    fig, axes = plt.subplots(1, 2)

    axes[0].imshow(data.reshape(28,28,1), interpolation='nearest')
    axes[0].title.set_text("predicted " + str(np.argmax(model.predict(data))))
    vals = [x for x in model.predict(data)[0]]
    
    axes[1].title.set_text("model predictions:")
    axes[1].bar([str(x) for x in range(len(vals))] ,vals)
    
    # creating the Tkinter canvas
    # containing the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig,
                               master = window)  
    canvas.draw()
  
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().grid(row=0, column=2, pady=2, sticky=W, )

  
with open(MODEL_PATH, "rb") as file:
    (model, loss_history) = pk.load(file)


def predict_digit(img, window):
    #resize image to 28x28 pixels
    img = img.resize((28,28))
    #convert rgb to grayscale
    img = img.convert('L')
    img = np.array(img)
    #reshaping to support our model input and normalizing
    img = img.reshape(1,28,28,1)
    img = img/255.0
    img = 1-img
    #predicting the class
    res = model.predict(img)[0]
    predict_image_sample(img, model, window)
    return np.argmax(res), max(res)

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.x = self.y = 0

        # Creating elements
        self.canvas = tk.Canvas(self, width=300, height=300, bg = "yellow", cursor="cross",border=3, borderwidth=3)
        self.label = tk.Label(self, text="Thinking..", font=("Helvetica", 48))
        self.classify_btn = tk.Button(self, text = "Recognise", command =         self.classify_handwriting) 
        self.button_clear = tk.Button(self, text = "Clear", command = self.clear_all)

        # Grid structure
        self.canvas.grid(row=0, column=0, pady=2, sticky=W, )
        self.label.grid(row=0, column=1,pady=2, padx=2)
        self.classify_btn.grid(row=1, column=1, pady=2, padx=2)
        self.button_clear.grid(row=1, column=0, pady=2)

        #self.canvas.bind("<Motion>", self.start_pos)
        self.canvas.bind("<B1-Motion>", self.draw_lines)
        self.canvas.bind("<ButtonRelease-1>", self.classify_handwriting)

    def clear_all(self):
        self.canvas.delete("all")

    def classify_handwriting(self, event=None):
        HWND = self.canvas.winfo_id() # get the handle of the canvas
        rect = win32gui.GetWindowRect(HWND) # get the coordinate of the canvas
        im = ImageGrab.grab(rect)
        
        digit, acc = predict_digit(im, self)
        self.label.configure(text= str(digit)+', '+ str(int(acc*100))+'%')

    def draw_lines(self, event):
        self.x = event.x
        self.y = event.y
        r=8
        self.canvas.create_oval(self.x-r, self.y-r, self.x + r, self.y + r, fill='black')

app = App()
mainloop()