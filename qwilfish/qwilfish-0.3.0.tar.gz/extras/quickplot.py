import sqlite3
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

class PlotApp():

    def __init__(self):
        self.current_db = None
        self.x_values = None
        self.y_values = None
        self.figure = None
        self.canvas = None
        self.root = tk.Tk()
        self.root.title("Quickplot!")
        self.place_widgets(self.root)
        self.bind_shortcut_keys()

    def place_widgets(self, parent):
        self.confFrame = ttk.Frame(parent)
        self.confFrame.grid()
        self.canvasFrame = ttk.Frame(parent)
        self.canvasFrame.grid()

        self.place_conf_panel(self.confFrame)
        self.place_matplotlib_figure(self.canvasFrame)

    def place_conf_panel(self, parent):
        self.place_db_button(parent)
        self.place_x_axis_radiobuttons(parent)
        self.place_y_axis_dropdown(parent)
        self.place_plot_button(parent)

    def place_db_button(self, parent):
        def browse():
            filename = tk.filedialog.askopenfilename(
                initialdir="~",
                filetypes=(("SQLite database", "*.db"),
                           ("All files", "*.*")))

            if filename:
                self.current_db = filename
                self.current_db_label.configure(
                    text=f"Selected: {self.current_db}")
            else:
                self.current_db = None
                self.current_db_label.configure(
                    text=f"No file selected")

        self.current_db_label = ttk.Label(parent, text="No file selected")
        button = ttk.Button(parent, text="Browse", command=browse)
        self.current_db_label.grid()
        button.grid()

    def place_x_axis_radiobuttons(self, parent):
        self.x_values = tk.StringVar(parent)

        r1 = ttk.Radiobutton(parent,
                            text="Case number",
                            variable=self.x_values,
                            value="caseno")
        r2 = ttk.Radiobutton(parent,
                            text="Timestamp",
                            variable=self.x_values,
                            value="timestamp")

        r1.grid()
        r2.grid()
        r1.invoke()

    def place_y_axis_dropdown(self, parent):
        def get_columns():
            if self.current_db:
                conn = sqlite3.connect(self.current_db)
                c = conn.cursor()
                # Get the tables from the database
                c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                column_names = []
                for t in c.fetchall():
                    cols = c.execute(f"PRAGMA table_info({t[0]});")
                    for col in cols:
                        column_names.append(f"{t[0]}:{col[1]}")
                c.close()
                conn.close()
                return column_names
            else:
                return []

        self.y_values = tk.StringVar(parent)
        y_menu = ttk.Combobox(
            parent,
            state="readonly",
            width=70,
            textvariable=self.y_values,
            postcommand=lambda: y_menu.configure(values=get_columns()))
        y_menu.grid()

    def place_plot_button(self, parent):
        def plot():
            conn = sqlite3.connect(self.current_db)
            c = conn.cursor()

            c.execute("SELECT name FROM sqlite_master WHERE name GLOB 'main_results*';")
            x_table = c.fetchone()[0]
            x_col = self.x_values.get()
            y_table, y_col = self.y_values.get().split(":")

            c.execute(f"SELECT \"{x_col}\" FROM \"{x_table}\"")
            x = [data[0] for data in c.fetchall()]
            c.execute(f"SELECT \"{y_col}\" FROM \"{y_table}\";")
            y = [data[0] for data in c.fetchall()]
            c.close()
            conn.close()

            self.figure.clear()
            plot = self.figure.add_subplot(1, 1, 1)
            plot.set_xlabel(x_col)
            plot.set_ylabel(y_col)
            plot.plot(x, y, color="red", linestyle="-")
            self.canvas.draw()

        button = ttk.Button(parent, text="Plot!", command=plot)
        button.grid()

    def place_matplotlib_figure(self, parent):
        self.figure = Figure(figsize=(8,8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().grid()

    def bind_shortcut_keys(self):
        self.root.bind("<Control-q>", self.quit)
        self.root.bind("<Control-w>", self.quit)

    def start(self):
        self.root.mainloop()

    def quit(self, e):
        self.root.destroy()

if __name__ == "__main__":
    #main()
    app = PlotApp()
    app.start()
