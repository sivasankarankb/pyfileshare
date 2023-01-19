import math
import time
import statistics
import pathlib

import tkinter as tk
from tkinter import ttk

import tkutils
import format_size

import preferences

class Downloader:
    def __init__(self):
        self.__client = None
        self.__tasklist = None

        self.__dl_updates = []
        self.__dl_tasks = {}
        self.__tasklist_current_selection = None

        self.__icon_done = tkutils.load_icon('icons/done.png')
        self.__icon_broken = tkutils.load_icon('icons/broken_file.png')

        self.__icon_pause_all = tkutils.load_icon('icons/pause_all.png')
        self.__icon_resume_all = tkutils.load_icon('icons/resume_all.png')

        self.__icon_pause = tkutils.load_icon('icons/pause.png')
        self.__icon_resume = tkutils.load_icon('icons/resume.png')

        self.__icon_cancel = tkutils.load_icon('icons/cancel.png')
        self.__icon_clear = tkutils.load_icon('icons/clear.png')

        self.__tasksframe = ttk.Frame(master=None)

        self.__tasklist_pauseall_button = ttk.Button(
            master=self.__tasksframe, text='Pause All',
            command=self.__tasklist_pauseall_click,
            image=self.__icon_pause_all,
        )

        self.__tasklist_pauseall_button.grid(
            row=0, column=0, sticky=tk.E, padx=4
        )

        self.__tasklist_resumeall_button = ttk.Button(
            master=self.__tasksframe, text='Resume All',
            command=self.__tasklist_resumeall_click,
            image=self.__icon_resume_all
        )

        self.__tasklist_resumeall_button.grid(
            row=0, column=1, sticky=tk.W, padx=4
        )

        self.__tasklist_pauseone_button = ttk.Button(
            master=self.__tasksframe, text='Pause',
            command=self.__tasklist_pauseone_click,
            image=self.__icon_pause
        )

        self.__tasklist_pauseone_button.grid(
            row=0, column=2, sticky=tk.W, padx=4
        )

        self.__tasklist_resumeone_button = ttk.Button(
            master=self.__tasksframe, text='Resume',
            command=self.__tasklist_resumeone_click,
            image=self.__icon_resume
        )

        self.__tasklist_resumeone_button.grid(
            row=0, column=3, sticky=tk.W, padx=4
        )

        self.__tasklist_cancelone_button = ttk.Button(
            master=self.__tasksframe, text='Cancel',
            command=self.__tasklist_cancelone_click,
            image=self.__icon_cancel
        )

        self.__tasklist_cancelone_button.grid(
            row=0, column=4, sticky=tk.W, padx=4
        )

        self.__tasklist_clearcomplete_button = ttk.Button(
            master=self.__tasksframe, text='Clear',
            command=self.__tasklist_clearcomplete_click,
            image=self.__icon_clear
        )

        self.__tasklist_clearcomplete_button.grid(
            row=0, column=5, sticky=tk.W, padx=4
        )

        self.__tasklist = tkutils.create_treeview(
            self.__tasksframe, ('Name', 'Progress', 'Speed')
        )

        self.__tasklist.grid(
            row=1, column=0, columnspan=6, sticky=tk.NSEW, pady=(8, 0)
        )

        self.__tasklist_scrollbar = ttk.Scrollbar(
            self.__tasksframe, orient='vertical'
        )

        self.__tasklist_scrollbar.grid(
            row=1, column=6, sticky=tk.NS, pady=(8, 0), padx=(8, 0)
        )

        self.__tasklist_scrollbar['command'] = self.__tasklist.yview
        self.__tasklist['yscrollcommand'] = self.__tasklist_scrollbar.set

        self.__tasksframe.grid_rowconfigure(1, weight=1)
        self.__tasksframe.grid_columnconfigure(0, weight=1)
        self.__tasksframe.grid_columnconfigure(5, weight=1)

        self.__tasklist.bind('<<TreeviewSelect>>', self.__tasklist_select)

        self.__single_task_buttons_update()
        self.__all_tasks_buttons_update()

        self.__prefs = preferences.get_instance()

    def get_container(self): return self.__tasksframe

    def set_client(self, client):
        self.__client = client
        self.__client.getfile_monitor_silence(self.__download_progress_pre)

    def notify_file_browser_connected(self):
        self.__client.getfile_monitor_silence(self.__download_progress)
        self.__render_silenced_updates()

    def clear_tasks_list(self):
        self.__tasklist_current_selection = None
        self.__dl_tasks = []

        for child in self.__tasklist.get_children():
            self.__tasklist.delete(child)

        self.__single_task_buttons_update()
        self.__all_tasks_buttons_update()

    def __single_task_buttons_update(self, task=None):
        if task != None:
            if task in self.__dl_tasks:
                task = self.__dl_tasks[task]
            else: return

        if task == None or task['done']:
            tkutils.disable_widget(self.__tasklist_pauseone_button)
            tkutils.disable_widget(self.__tasklist_resumeone_button)
            tkutils.disable_widget(self.__tasklist_cancelone_button)

        elif task['paused']:
            tkutils.disable_widget(self.__tasklist_pauseone_button)
            tkutils.enable_widget(self.__tasklist_resumeone_button)
            tkutils.enable_widget(self.__tasklist_cancelone_button)

        else:
            tkutils.enable_widget(self.__tasklist_pauseone_button)
            tkutils.disable_widget(self.__tasklist_resumeone_button)
            tkutils.enable_widget(self.__tasklist_cancelone_button)

    def __all_tasks_buttons_update(self):
        paused, resumed, done = False, False, False

        for task in self.__dl_tasks:
            if self.__dl_tasks[task]['done']: done = True
            elif self.__dl_tasks[task]['paused']: paused = True
            else: resumed = True

        if paused: tkutils.enable_widget(self.__tasklist_resumeall_button)
        else: tkutils.disable_widget(self.__tasklist_resumeall_button)

        if resumed: tkutils.enable_widget(self.__tasklist_pauseall_button)
        else: tkutils.disable_widget(self.__tasklist_pauseall_button)

        if done: tkutils.enable_widget(self.__tasklist_clearcomplete_button)
        else: tkutils.disable_widget(self.__tasklist_clearcomplete_button)

    def __tasklist_select(self, event):
        sel = self.__tasklist.selection()

        if len(sel) == 0: self.__tasklist_current_selection = None
        else: self.__tasklist_current_selection = sel[0]

        self.__single_task_buttons_update(self.__tasklist_current_selection)

    def __tasklist_pauseall_click(self): self.__client.getfile_pause()

    def __tasklist_resumeall_click(self): self.__client.getfile_resume()

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
        self.__all_tasks_buttons_update()

    def download_file(self, path, name):
        params = {}

        dest = self.__prefs.get_download_dest()

        if dest != None:
            d = pathlib.Path(dest).resolve()

            if d.exists() and d.is_dir():
                d = d / name
                params['saveto'] = str(d)

        self.__client.getfile(path, **params)

    def __update_task(self, key, name, values=None, image=None):
        params = {}

        if values != None: params['values'] = values
        if image != None: params['image'] = image

        if self.__tasklist.exists(key):
            self.__tasklist.item(key, text=name, **params)

        else: self.__tasklist.insert('', 'end', iid=key, text=name, **params)

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
            self.__update_task(path, tname, ('Failed', self.__icon_broken))
            self.__dl_tasks[path]['done'] = True

        elif status == 'filedone':
            self.__update_task(path, tname, ('Done'), self.__icon_done)
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
            rate = format_size.shortensize(rate) +'/s'
            percent = self.__download_progress_percent(data)

            self.__update_task(path, tname, (percent, rate))
            self.__dl_tasks[path]['lastupdated'] = time.monotonic()
            self.__dl_tasks[path]['timestaken'] = []

        elif status == 'filecanceled':
            self.__update_task(path, tname, ('Cancelled'))
            self.__dl_tasks[path]['done'] = True

        if self.__tasklist_current_selection == path:
            self.__single_task_buttons_update(path)

        self.__all_tasks_buttons_update()

    def __render_silenced_updates(self):
        if len(self.__dl_updates) > 0:
            for update in self.__dl_updates:
                self.__download_progress(update)
            self.__dl_updates = []

        else:
            self.__single_task_buttons_update()
            self.__all_tasks_buttons_update()
