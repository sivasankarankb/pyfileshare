#!/usr/bin/env python3

import math
import time
import statistics

import tkinter as tk
from tkinter import ttk

from pyfs_client import PyFSClient

#TODO:
# Add pause, resume, cancel, delete, and pause, resume and delete all buttons
# Add scrollbars to file and task lists
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

    def __disable_widget(self, widget): widget.state(('disabled',))

    def __enable_widget(self, widget): widget.state(('!disabled',))

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

        self.__panes.grid(
            row=0, column=0, sticky=tk.NSEW, pady=8, padx=8
        )

        self.__mainframe.grid_rowconfigure(0, weight=1)
        self.__mainframe.grid_columnconfigure(0, weight=1)

        self.__panes.insert('end', self.__filesframe)
        self.__panes.insert('end', self.__tasksframe)

        self.__filelist_back_button = ttk.Button(
            master=self.__filesframe, text='Back', command=self.__filelist_back
        )

        self.__filelist_back_button.grid(row=0, column=0, sticky=tk.W)
        self.__disable_widget(self.__filelist_back_button)

        self.__filelist = self.__create_treeview(
            self.__filesframe, ('Name', 'Size', 'Created', 'Modified')
        )

        self.__filelist.grid(row=1, column=0, sticky=tk.NSEW, pady=(8, 0))
        self.__filesframe.grid_rowconfigure(1, weight=1)
        self.__filesframe.grid_columnconfigure(0, weight=1)

        self.__tasklist_pauseall_button = ttk.Button(
            master=self.__tasksframe, text='Pause All',
            command=self.__client.getfile_pause
        )

        self.__tasklist_pauseall_button.grid(row=0, column=0, sticky=tk.E)
        self.__disable_widget(self.__tasklist_pauseall_button)

        self.__tasklist_resumeall_button = ttk.Button(
            master=self.__tasksframe, text='Resume All',
            command=self.__client.getfile_resume
        )

        self.__tasklist_resumeall_button.grid(row=0, column=1, sticky=tk.W)
        self.__disable_widget(self.__tasklist_resumeall_button)

        self.__tasklist_pauseone_button = ttk.Button(
            master=self.__tasksframe, text='Pause',
            command=self.__tasklist_pauseone_click
        )

        self.__tasklist_pauseone_button.grid(row=0, column=2, sticky=tk.W)
        self.__disable_widget(self.__tasklist_pauseone_button)

        self.__tasklist_resumeone_button = ttk.Button(
            master=self.__tasksframe, text='Resume',
            command=self.__tasklist_resumeone_click
        )

        self.__tasklist_resumeone_button.grid(row=0, column=3, sticky=tk.W)
        self.__disable_widget(self.__tasklist_resumeone_button)

        self.__tasklist_cancelone_button = ttk.Button(
            master=self.__tasksframe, text='Cancel',
            command=self.__tasklist_cancelone_click
        )

        self.__tasklist_cancelone_button.grid(row=0, column=4, sticky=tk.W)
        self.__disable_widget(self.__tasklist_cancelone_button)

        self.__tasklist_clearcomplete_button = ttk.Button(
            master=self.__tasksframe, text='Clear',
            command=self.__tasklist_clearcomplete_click
        )

        self.__tasklist_clearcomplete_button.grid(row=0, column=5, sticky=tk.W)
        self.__disable_widget(self.__tasklist_clearcomplete_button)

        self.__tasklist = self.__create_treeview(
            self.__tasksframe, ('Name', 'Progress', 'Speed')
        )

        self.__tasklist.grid(
            row=1, column=0, columnspan=6, sticky=tk.NSEW, pady=(8, 0)
        )

        self.__tasksframe.grid_rowconfigure(1, weight=1)
        self.__tasksframe.grid_columnconfigure(0, weight=1)
        self.__tasksframe.grid_columnconfigure(5, weight=1)

        self.__client.getfile_monitor_silence(self.__download_progress)
        for update in self.__dl_updates: self.__download_progress(update)

        # was bound to <TreeviewSelect>
        self.__filelist.bind('<Double-ButtonPress-1>', self.__filelist_select)

        self.__tasklist_current_selection = None
        self.__tasklist.bind('<<TreeviewSelect>>', self.__tasklist_select)

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

    def __tasklist_select(self, event):
        sel = self.__tasklist.selection()

        if len(sel) == 0: # TODO: Handle deselect
            self.__tasklist_current_selection = None

        else: # TODO: Handle select (e.g. button enabling)
            self.__tasklist_current_selection = sel[0]

    def __tasklist_pauseone_click(self):
        sel = self.__tasklist_current_selection

        if sel != None and sel in self.__dl_tasks:
            paused = self.__dl_tasks[sel]['paused']
            done = self.__dl_tasks[sel]['done']

            if not (paused or done): self.__client.getfile_pause(sel)

    def __tasklist_resumeone_click(self):
        sel = self.__tasklist_current_selection

        if sel != None and sel in self.__dl_tasks:
            resumed = not self.__dl_tasks[sel]['paused']
            done = self.__dl_tasks[sel]['done']

            if not (resumed or done): self.__client.getfile_resume(sel)

    def __tasklist_cancelone_click(self):
        sel = self.__tasklist_current_selection

        if sel != None and sel in self.__dl_tasks:
            if not self.__dl_tasks[sel]['done']:
                self.__client.getfile_cancel(sel)

    def __tasklist_clearcomplete_click(self):
        remaining = {}

        for path, task in self.__dl_tasks.items():
            if task['done']: self.__tasklist.delete(path)
            else: remaining[path] = task

        self.__dl_tasks = remaining

    def __update_task(self, key, name, values=None):

        if self.__tasklist.exists(key):
            if values != None: self.__tasklist.item(
                key, text=name, values=values
            )

            else: self.__tasklist.insert(key, text=name, values=())

        else:

            if values != None: self.__tasklist.insert(
                '', 'end', iid=key, text=name, values=values
            )

            else: self.__tasklist.insert('', 'end', iid=key, text=name)

    def __download_progress_pre(self, data): self.__dl_updates.append(data)

    def __download_progress_percent(self, data):
        numerator = data['partdone'] + 1
        denominator = data['partmax'] + 1
        percent = math.floor(100 * numerator/ denominator)
        return str(percent) + '%'

    def __download_progress(self, data):
        if 'status' not in data: return

        status = data['status']

        if 'path' in data: path = data['path']
        else: path = ''

        if path in self.__dl_tasks: tname = self.__dl_tasks[path]['name']

        elif 'name' in data:
            self.__dl_tasks[path] = {
                'name': data['name'], 'lastupdated': time.monotonic(),
                'timestaken': [], 'done': False, 'paused': False
            }

            tname = data['name']

        else: tname = path

        if status == 'filestarted':
            self.__update_task(path, tname, ('Started'))

        elif status == 'fileerror':
            self.__update_task(path, tname, ('Failed'))
            self.__dl_tasks[path]['done'] = True

        elif status == 'filedone':
            self.__update_task(path, tname, ('Done'))
            self.__dl_tasks[path]['done'] = True

        elif status == 'filepaused':
            percent = self.__download_progress_percent(data)
            self.__update_task(path, tname, (percent, 'Paused'))
            self.__dl_tasks[path]['paused'] = True

        elif status == 'fileresumed':
            percent = self.__download_progress_percent(data)
            self.__update_task(path, tname, (percent, 'Resumed'))
            self.__dl_tasks[path]['paused'] = False

        elif status == 'fileprogress':
            self.__dl_tasks[path]['timestaken'].append(data['timetaken'])

            if time.monotonic() - self.__dl_tasks[path]['lastupdated'] < 0.1:
                return

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
            percent = self.__download_progress_percent(data)

            self.__update_task(path, tname, (percent, rate))
            self.__dl_tasks[path]['lastupdated'] = time.monotonic()
            self.__dl_tasks[path]['timestaken'] = []

        elif status == 'filecanceled':
            self.__update_task(path, tname, ('Cancelled'))
            self.__dl_tasks[path]['done'] = True

    def __exit(self):
        if not self.__exit_in_progress:
            self.__exit_in_progress = True
            self.__client.getfile_pause()
            self.__client.cleanup()
            self.__tk.destroy()

if __name__ == '__main__':
    app = Application()
    app.start()
