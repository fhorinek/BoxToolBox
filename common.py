
import json
import os

import shutil

calibrate_win_w = 800
calibrate_win_h = 600

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog


config_file = "BoxToolBox.json"

def load_config(path):
    cfg_file = os.path.join(path, config_file)
    if os.path.exists(cfg_file):
        f = open(cfg_file, "r")
        try:
            cfg = json.load(f)
        except:
            cfg = {}

        f.close()
        
        return cfg
    return {}
    
    

def store_config(cfg, path):
    cfg_file = os.path.join(path, config_file)
    f = open(cfg_file, "w")
    cfg = json.dump(cfg, f, sort_keys=True, indent=4, separators=(',', ': '))
    f.close()

def read_dir(path):
    lst = os.listdir(path)
    lst.sort()

    images = []
    
    for file in lst:
        ext = os.path.basename(file).split(".")
        if len(ext) == 2:
            if ext[1].upper() == "JPG":
                images.append(file)

    return images

def get_dir():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title="Select folder with images", mustexist = True)   
    
def create_progressbar():
    ws = tk.Tk()
    ws.title('BoxToolBox')
    ws.geometry('200x80')
    ws.resizable(False, False)
    ws.eval('tk::PlaceWindow . center')
    ws.deiconify()

    title = ttk.Label(ws)
    title.pack(expand=True)

    text = ttk.Label(ws)
    text.pack(expand=True)

    bar = ttk.Progressbar(ws, orient=tk.HORIZONTAL, length=150, mode='determinate')
    bar.pack(expand=True)
    
    return [ws, title, text, bar]
    
def update_progressbar(win, title, text, progress):
    win[1]["text"] = title
    win[2]["text"] = text
    win[3]["value"] = progress
    win[0].update_idletasks()

def close_progressbar(win):
    win[0].destroy()
    
    
def clear_dir(path):
    try:
        shutil.rmtree(path)
    except:
        pass

