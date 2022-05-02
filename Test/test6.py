import multiprocessing
import os
import sys
import csv
import time
import random
import numpy as np
import tkinter as tk
from vedo import *
from datetime import datetime
from tkinter import filedialog


def toggle_state(action):
    print(action)


def update_clock(text_box: tk.Text):
    now = time.strftime("%H:%M:%S\n")
    text_box.insert(tk.END, now)
    text_box.after(1000, lambda: update_clock(text_box))


def get_values(root, field_entries):
    try:
        for field_entry in field_entries:
            print(field_entries[field_entry]['data'].get())
        root.destroy()
    except Exception as e:
        print(e)


def gui_main():
    root = tk.Tk()
    root.title('Vehicle Attribute Selection')
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=4)

    fields = {
        0: {'data': tk.StringVar(), 'default': '___', 'name': 'Enter the required vehicle parameters'},
        1: {'data': tk.StringVar(), 'default': '1.0', 'name': 'Back Overhang'},
        2: {'data': tk.StringVar(), 'default': '1.0', 'name': 'Front Overhang'},
        3: {'data': tk.StringVar(), 'default': '1.0', 'name': 'Wheel Radius'},
        4: {'data': tk.StringVar(), 'default': '4',   'name': 'Number of wheels'},
        5: {'data': tk.StringVar(), 'default': '1.0', 'name': 'Base Length'},
        6: {'data': tk.StringVar(), 'default': '1.0', 'name': 'Vehicle Width'}
    }

    for i in range(0, 7):
        tk.Label(root, text=fields[i]['name'], borderwidth=2, font=10
                 ).grid(column=0, row=i, sticky=tk.W, padx=5, pady=5)
        if i != 0:
            ent = tk.Entry(root, textvariable=fields[i]['data'])
            ent.insert(tk.END, fields[i]['default'])
            ent.grid(column=1, row=i, sticky=tk.E, padx=5, pady=5)
    tk.Button(root, text='Confirm', command=lambda: get_values(root, fields)
              ).grid(column=1, row=len(fields), sticky=tk.E, padx=5, pady=5)
    root.mainloop()

##
##


gui_main()
