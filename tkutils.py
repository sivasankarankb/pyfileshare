import tkinter as tk
from tkinter import ttk

def create_treeview(master, columns):
    treeview = ttk.Treeview(master=master)
    treeview['selectmode'] = 'browse'
    treeview['columns'] = columns[1:]
    treeview.heading('#0', text=columns[0])

    for column in columns[1:]:
        treeview.heading(column, text=column)

    return treeview

def disable_widget(widget): widget.state(('disabled',))

def enable_widget(widget): widget.state(('!disabled',))

def load_icon(path):
    try: return tk.PhotoImage(file=path)
    except: return None