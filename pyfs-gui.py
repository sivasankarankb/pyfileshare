#!/usr/bin/env python3

import math
import time
import statistics

import tkinter as tk
from tkinter import ttk

from pyfs_client import PyFSClient

#TODO:
# App not exiting when downloads active
# Add pause, resume, cancel, delete, and pause, resume and delete all buttons
# Add entry (text box) for address bar and a go button
# Query and display file size, created and modified dates

#DONE:
# Move toolbar into panes
# Pause active downloads when exiting and not autoresume them
# Multiple downloads progress messup
# Increase download speed update interval
# KeyError in resume status receive - Add __dl_tasks entry on app restart

class Application:
    def __create_treeview(self, master, columns):
        treeview = ttk.Treeview(master=master)
        treeview['selectmode'] = 'browse'
        treeview['columns'] = columns[1:]
        treeview.heading('#0', text=columns[0])

        for column in columns[1:]:
            treeview.heading(column, text=column)

        return treeview

    def __init__(self):
        self.__tasklist = None
        self.__dl_updates = []
        self.__dl_tasks = {}

        self.__client = PyFSClient('http://127.0.0.1:8080', 'progress.shelf')
        self.__client.getfile_monitor_silence(self.__download_progress_pre)

        self.__tk = tk.Tk()
        self.__tk.grid_rowconfigure(0, weight=1)
        self.__tk.grid_columnconfigure(0, weight=1)

        self.__tk.protocol("WM_DELETE_WINDOW", self.__exit)
        self.__exit_in_progress = False

        self.__mainframe = ttk.Frame(master=self.__tk)
        self.__mainframe.grid(sticky=tk.NSEW)

        self.__filesframe = ttk.Frame(master=None)
        self.__tasksframe = ttk.Frame(master=None)

        self.__panes = ttk.PanedWindow(
            master=self.__mainframe, orient='horizontal'
        )

        self.__panes.grid(row=0, column=0, sticky=tk.NSEW)

        self.__mainframe.grid_rowconfigure(0, weight=1)
        self.__mainframe.grid_columnconfigure(0, weight=1)

        self.__panes.insert('end', self.__filesframe)
        self.__panes.insert('end', self.__tasksframe)

        self.__filelist_back_button = ttk.Button(
            master=self.__filesframe, text='<-', command=self.__filelist_back
        )

        self.__filelist_back_button.grid(row=0, column=0, sticky=tk.W)

        self.__filelist = self.__create_treeview(
            self.__filesframe, ('Name', 'Size', 'Created', 'Modified')
        )

        self.__filelist.grid(row=1, column=0, sticky=tk.NSEW)
        self.__filesframe.grid_rowconfigure(1, weight=1)
        self.__filesframe.grid_columnconfigure(0, weight=1)

        self.__tasklist_pause_button = ttk.Button(
            master=self.__tasksframe, text='||',
            command=self.__client.getfile_pause
        )

        self.__tasklist_pause_button.grid(row=0, column=0, sticky=tk.W)

        self.__tasklist_resume_button = ttk.Button(
            master=self.__tasksframe, text='|>',
            command=self.__client.getfile_resume
        )

        self.__tasklist_resume_button.grid(row=0, column=1, sticky=tk.W)

        self.__tasklist = self.__create_treeview(
            self.__tasksframe, ('Name', 'Progress', 'Speed')
        )

        self.__tasklist.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
        self.__tasksframe.grid_rowconfigure(1, weight=1)
        self.__tasksframe.grid_columnconfigure(1, weight=1)

        self.__client.getfile_monitor_silence(self.__download_progress)
        for update in self.__dl_updates: self.__download_progress(update)

        # was bound to <TreeviewSelect>
        self.__filelist.bind('<Double-ButtonPress-1>', self.__filelist_select)

        listing = self.__client.list()
        self.__listings = [listing]
        self.__display_listing()

    def start(self):
        self.__tk.mainloop()

    def __display_listing(self):
        for child in self.__filelist.get_children():
            self.__filelist.delete(child)

        listing = self.__listings[-1]

        if 'dirs' in listing['info']:
            for dir in listing['info']['dirs']:
                self.__filelist.insert('', 'end', iid=dir, text=dir)

        if 'files' in listing['info']:
            for file in listing['info']['files']:
                self.__filelist.insert('', 'end', iid=file, text=file)

    def __filelist_back(self):
        if len(self.__listings) > 1:
            self.__listings.pop()
            self.__display_listing()

    def __filelist_select(self, event):
        sel = self.__filelist.selection()
        if len(sel) == 0: return # Deselect

        sel = sel[0]
        info = self.__listings[-1]['info']
        path = info['path'] + sel

        if 'dirs' in info and sel in info['dirs']:
            listing = self.__client.list(path)

            if listing != None and listing['status'] == 'ok':
                self.__listings.append(listing)
                self.__display_listing()

        elif 'files' in info and sel in info['files']:
            self.__client.getfile(path)

    def __update_task(self, key, name, values=None):
        index = 'end'

        if self.__tasklist.exists(key):
            index = self.__tasklist.index(key)
            self.__tasklist.delete(key)

        if values != None: self.__tasklist.insert(
            '', index, iid=key, text=name, values=values
        )

        else: self.__tasklist.insert('', index, iid=key, text=name)

    def __download_progress_pre(self, data): self.__dl_updates.append(data)

    def __download_progress(self, data):
        if 'status' not in data: return

        status = data['status']

        if 'path' in data: path = data['path']
        else: path = ''

        if path in self.__dl_tasks: tname = self.__dl_tasks[path]['name']

        elif 'name' in data:
            self.__dl_tasks[path] = {
                'name': data['name'], 'lastupdated': time.monotonic(),
                'timestaken': []
            }

            tname = data['name']

        else: tname = path

        if status == 'filestarted':
            self.__update_task(path, tname, ('Started'))

        elif status == 'fileerror': self.__update_task(path, tname, ('Failed'))

        elif status == 'filedone': self.__update_task(path, tname, ('Done'))

        elif status == 'filepaused':
            self.__update_task(path, tname, ('Paused'))

        elif status == 'fileresumed':
            self.__update_task(path, tname, ('Resumed'))

        elif status == 'fileprogress':
            self.__dl_tasks[path]['timestaken'].append(data['timetaken'])

            if time.monotonic() - self.__dl_tasks[path]['lastupdated'] < 0.1:
                return

            numerator = data['partdone'] + 1
            denominator = data['partmax'] + 1
            percent = math.floor(100 * numerator/ denominator)

            timetakenavg = statistics.mean(self.__dl_tasks[path]['timestaken'])
            rate = data['partsize'] / timetakenavg
            rateunit = 'B'

            if rate >= 1024:
                rate /= 1024
                rateunit = 'KB'

            if rate >= 1024:
                rate /= 1024
                rateunit = 'MB'

            if rate >= 1024:
                rate /= 1024
                rateunit = 'GB'

            rate = str(round(rate, 2)) + rateunit +'/s'
            percent = str(percent) + '%'

            self.__update_task(path, tname, (percent, rate))
            self.__dl_tasks[path]['lastupdated'] = time.monotonic()
            self.__dl_tasks[path]['timestaken'] = []

    def __exit(self):
        if not self.__exit_in_progress:
            self.__exit_in_progress = True
            self.__client.getfile_pause()
            self.__client.cleanup()
            self.__tk.destroy()

if __name__ == '__main__':
    app = Application()
    app.start()
