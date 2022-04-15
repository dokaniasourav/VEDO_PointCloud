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


def gui_main():
    root = tk.Tk()
    # root.geometry('400x300')
    root.title('Main menu')

    label = tk.Label(root, text="Enter a value ", borderwidth=2, font=10)

    text = tk.StringVar()
    entry = tk.Entry(root, textvariable=text)
    # e.bind('<Key>', key_press)

    button_1 = tk.Button(root, text="Enter Slope AVG Mode", command=lambda: toggle_state('abc'))

    text_box = tk.Text(root, height=5, width=52)

    label.pack()
    entry.pack()
    button_1.pack()
    text_box.pack()

    update_clock(text_box)
    root.mainloop()


gui_main()