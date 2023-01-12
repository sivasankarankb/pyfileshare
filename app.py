#!/usr/bin/env python3

import math
import time
import statistics
import pathlib

import tkinter as tk
import tkinter.filedialog as tk_filedialog
from tkinter import ttk

from pyfs_client import PyFSClient

class AboutBox:
    def __init__(self, master):
        win = tk.Toplevel(master)
        win.title('About')
        win.transient(master)

        frame = ttk.Frame(win)
        frame.grid(padx=16, pady=16)

        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        
        l1 = ttk.Label(frame, text='pyfileshare')
        l1.grid(pady=(0,8))
        
        l2 = ttk.Label(frame, text='Version v0.1.1')
        l2.grid(pady=(0,8))

        l3 = ttk.Label(frame, text='https://github.com/sivasankarankb/pyfileshare')
        l3.grid(pady=(0,8))

        lcopy = ttk.Label(frame, text='Copyright (C) 2020-2023 Sivasankaran K B')
        lcopy.grid(pady=(0,20))

        license_txt ='''\
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation.'''

        llicense = ttk.Label(frame, text=license_txt)
        llicense.grid(pady=(0,20))

        l4 = ttk.Label(frame, text='-- Contributors --')
        l4.grid(pady=(0,20))

        ll = ttk.Label(frame, text='Icons: Sudharsanan K B')
        ll.grid(pady=(0,8))

        frame.columnconfigure(0, weight=1)

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

    def __load_icon(self, path):
        try: return tk.PhotoImage(file=path)
        except: return None

    def __init__(self):
        self.__client = None
        self.__tasklist = None

        self.__listings = []
        self.__listings_forward = []

        self.__dl_updates = []
        self.__dl_tasks = {}
        self.__tasklist_current_selection = None
        self.__server_addr = ''

        self.__tk = tk.Tk()
        self.__tk.withdraw()

        screenwidth = self.__tk.winfo_screenwidth()
        screenheight = self.__tk.winfo_screenheight()

        width = min(int(0.95 * screenwidth), 1280)
        height = 600
        winleft = int((screenwidth - width) / 2)
        wintop = int((screenheight - height) / 2)

        width = str(width)
        height = str(height)
        winleft = str(winleft)
        wintop = str(wintop)

        geometry = '=' + width + 'x' + height + '+' + winleft + '+' + wintop
        self.__tk.geometry(geometry)
        self.__tk.deiconify()

        self.__tk.grid_rowconfigure(0, weight=1)
        self.__tk.grid_columnconfigure(0, weight=1)

        self.__icon_go = self.__load_icon('icons/go.png')
        self.__icon_disconnect = self.__load_icon('icons/disconnect.png')

        self.__icon_back = self.__load_icon('icons/backward.png')
        self.__icon_refresh = self.__load_icon('icons/refresh.png')
        self.__icon_forward = self.__load_icon('icons/forward.png')

        self.__icon_file = self.__load_icon('icons/file.png')
        self.__icon_folder = self.__load_icon('icons/folder.png')
        self.__icon_done = self.__load_icon('icons/done.png')
        self.__icon_broken = self.__load_icon('icons/broken_file.png')

        self.__icon_pause_all = self.__load_icon('icons/pause_all.png')
        self.__icon_resume_all = self.__load_icon('icons/resume_all.png')

        self.__icon_pause = self.__load_icon('icons/pause.png')
        self.__icon_resume = self.__load_icon('icons/resume.png')

        self.__icon_cancel = self.__load_icon('icons/cancel.png')
        self.__icon_clear = self.__load_icon('icons/clear.png')

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

        self.__style = ttk.Style()
        self.__style.configure('TButton', relief='solid')
        self.__style.configure('TEntry', relief='flat', padding=4)
        self.__style.configure('Treeview', rowheight=28)

        self.__filelist_back_button = ttk.Button(
            master=self.__filesframe, text='Back',
            command=self.__filelist_back, image=self.__icon_back
        )

        self.__filelist_back_button.grid(
            row=0, column=0, sticky=tk.E, padx=(0, 8)
        )
        self.__disable_widget(self.__filelist_back_button)

        self.__filelist_refresh_button = ttk.Button(
            master=self.__filesframe, text='Refresh',
            command=self.__filelist_refresh, image=self.__icon_refresh
        )

        self.__filelist_refresh_button.grid(row=0, column=1, padx=(0, 8))
        self.__disable_widget(self.__filelist_refresh_button)

        self.__filelist_forward_button = ttk.Button(
            master=self.__filesframe, text='Forward',
            command=self.__filelist_forward, image=self.__icon_forward
        )

        self.__filelist_forward_button.grid(row=0, column=2, sticky=tk.W)
        self.__disable_widget(self.__filelist_forward_button)

        self.__address_bar_value = tk.StringVar()
        self.__address_bar_value.set("http://host:8080")

        self.__filelist_address_bar = ttk.Entry(
            self.__filesframe, textvariable=self.__address_bar_value
        )

        self.__filelist_address_bar.grid(
            row=0, column=3, sticky=tk.EW, padx=8
        )

        self.__filelist_go_button = ttk.Button(
            master=self.__filesframe, text='Go', command=self.__filelist_go,
            image=self.__icon_go
        )

        self.__filelist_go_button.grid(row=0, column=4, sticky=tk.W)

        self.__filelist_address_bar.bind('<Return>', self.__address_bar_activate)

        self.__filelist = self.__create_treeview(
            self.__filesframe, ('Name', 'Size', 'Created', 'Modified')
        )

        self.__filelist.grid(
            row=1, column=0, columnspan=5, sticky=tk.NSEW, pady=(8, 0)
        )

        self.__filelist_scrollbar = ttk.Scrollbar(
            self.__filesframe, orient='vertical'
        )

        self.__filelist_scrollbar.grid(
            row=1, column=5, sticky=tk.NS, pady=(8, 0), padx=(8, 0)
        )

        self.__filelist_scrollbar['command'] = self.__filelist.yview
        self.__filelist['yscrollcommand'] = self.__filelist_scrollbar.set

        self.__filesframe.grid_rowconfigure(1, weight=1)
        self.__filesframe.grid_columnconfigure(3, weight=1)

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

        self.__tasklist = self.__create_treeview(
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

        self.__filelist.bind('<Double-ButtonPress-1>', self.__filelist_select)

        self.__tasklist.bind('<<TreeviewSelect>>', self.__tasklist_select)

        self.__single_task_buttons_update()
        self.__all_tasks_buttons_update()
        self.__set_title()

        self.__menubar = tk.Menu(self.__tk)

        file_menu = tk.Menu(self.__tk, tearoff=False)

        file_menu.add(
            tk.COMMAND, label='Exit', command=self.__exit
        )

        self.__menubar.add(
            tk.CASCADE, label='File', menu=file_menu
        )

        edit_menu = tk.Menu(self.__tk, tearoff=False)

        edit_menu.add(
            tk.COMMAND, label='Preferences', command=self.__pref_menu
        )

        self.__menubar.add(
            tk.CASCADE, label='Edit', menu=edit_menu
        )

        server_menu = tk.Menu(self.__tk, tearoff=False)

        server_menu.add(
            tk.COMMAND, label='Start Server', command=self.__start_server
        )

        server_menu.add(
            tk.COMMAND, label='Stop Server', command=self.__stop_server
        )

        self.__menubar.add(
            tk.CASCADE, label='Server', menu=server_menu
        )
        
        help_menu = tk.Menu(self.__tk, tearoff=False)
        
        help_menu.add(
            tk.COMMAND, label='About', command=self.__about_menu
        )
        
        self.__menubar.add(
            tk.CASCADE, label='Help', menu=help_menu,
        )

        self.__tk['menu'] = self.__menubar

        self.__prefs_load()

    def __set_title(self, title=''):
        if title != '': title = 'pyfileshare - ' + title
        else: title = 'pyfileshare'

        self.__tk.title(title)

    def start(self):
        self.__tk.mainloop()

    def connect_to(self, addr):
        if self.__client == None:
            self.__client = PyFSClient(addr, 'progress.shelf')
            self.__client.getfile_monitor_silence(self.__download_progress_pre)

        listing = self.__client.list()

        if listing == None:
            if not self.__client.server_ok(): self.__client = None
            self.__server_addr = ''
            return False

        self.__filelist_address_bar_state('disconnect')
        self.__listings = [listing]

        if not addr.endswith('/'): addr += '/'

        self.__server_addr = addr
        self.__display_listing()

        self.__client.getfile_monitor_silence(self.__download_progress)

        if len(self.__dl_updates) > 0:
            for update in self.__dl_updates: self.__download_progress(update)
            self.__dl_updates = []

        else:
            self.__single_task_buttons_update()
            self.__all_tasks_buttons_update()

        return True

    def __display_listing(self):
        if len(self.__listings) <= 1:
            self.__disable_widget(self.__filelist_back_button)
        else:
            self.__enable_widget(self.__filelist_back_button)

        for child in self.__filelist.get_children():
            self.__filelist.delete(child)

        if len(self.__listings_forward) > 0:
            self.__enable_widget(self.__filelist_forward_button)

        else: self.__disable_widget(self.__filelist_forward_button)

        if len(self.__listings) == 0:
            self.__disable_widget(self.__filelist_refresh_button)
            self.__set_title()
            return

        self.__enable_widget(self.__filelist_refresh_button)

        listing = self.__listings[-1]
        self.__set_title(self.__server_addr + listing['info']['path'])

        if 'dirs' in listing['info']:
            for dir in listing['info']['dirs']:
                self.__filelist.insert(
                    '', 'end', iid=dir, text=dir, image=self.__icon_folder
                )

        if 'files' in listing['info']:
            if 'fileinfo' in listing['info']:
                for file in listing['info']['files']:
                    if file in listing['info']['fileinfo']:
                        size = listing['info']['fileinfo'][file]['size']
                        created = listing['info']['fileinfo'][file]['created']
                        mod = listing['info']['fileinfo'][file]['modified']
                        values = (size, created, mod)

                    else: values = ('', '', '')

                    self.__filelist.insert(
                        '', 'end', iid=file, text=file, values=values,
                        image=self.__icon_file
                    )

    def __filelist_go(self):
        address = self.__address_bar_value.get()
        self.connect_to(address)

    def __filelist_address_bar_state(self, state):
        if state == 'disconnect':
            self.__filelist_go_button['text'] = 'Disconnect'
            self.__filelist_go_button['command'] = self.__disconnect
            self.__filelist_go_button['image'] = self.__icon_disconnect
            self.__disable_widget(self.__filelist_address_bar)

        elif state == 'go':
            self.__filelist_go_button['text'] = 'Go'
            self.__filelist_go_button['command'] = self.__filelist_go
            self.__filelist_go_button['image'] = self.__icon_go
            self.__enable_widget(self.__filelist_address_bar)

    def __address_bar_activate(self, event): self.__filelist_go()

    def __filelist_back(self):
        if len(self.__listings) > 1:
            self.__listings_forward.append(self.__listings.pop())
            self.__filelist_refresh()
            self.__display_listing()

    def __filelist_forward(self):
        if len(self.__listings_forward) > 0:
            self.__listings.append(self.__listings_forward.pop())
            self.__filelist_refresh()
            self.__display_listing()

    def __filelist_refresh(self):
        if len(self.__listings) == 0: return

        path = self.__listings[-1]['info']['path']
        listing = self.__client.list(path)

        if listing != None and listing['status'] == 'ok':
            self.__listing_fetch_details(listing)
            self.__listings.pop()
            self.__listings.append(listing)
            self.__display_listing()

    def __listing_fetch_details(self, listing):
        if 'files' in listing['info']:
            listing['info']['fileinfo'] = {}

            for file in listing['info']['files']:
                path = listing['info']['path'] + file
                fileinfo = self.__client.list(path)
                infmt = '%j%Y%H%M%S%z'
                outfmt = '%a %d %b %Y, %I:%M:%S %p'

                if fileinfo != None and fileinfo['status'] == 'ok':
                    parsedinfo = {}
                    size = fileinfo['info']['size']
                    parsedinfo['size'] = self.__shortensize(size)

                    moment = fileinfo['info']['created']
                    moment = time.strptime(moment, infmt)
                    moment = time.strftime(outfmt, moment)
                    parsedinfo['created'] = moment

                    moment = fileinfo['info']['modified']
                    moment = time.strptime(moment, infmt)
                    moment = time.strftime(outfmt, moment)
                    parsedinfo['modified'] = moment

                    listing['info']['fileinfo'][file] = parsedinfo

    def __filelist_select(self, event):
        sel = self.__filelist.selection()
        if len(sel) == 0: return # Deselect

        sel = sel[0]
        info = self.__listings[-1]['info']
        path = info['path'] + sel

        if 'dirs' in info and sel in info['dirs']:
            listing = self.__client.list(path)

            if listing != None and listing['status'] == 'ok':
                if len(self.__listings_forward) > 0:
                    fwdpath = self.__listings_forward[-1]['info']['path'][:-1]
                    if fwdpath == path: self.__listings_forward.pop()
                    else: self.__listings_forward = []

                self.__listing_fetch_details(listing)
                self.__listings.append(listing)
                self.__display_listing()

        elif 'files' in info and sel in info['files']:
            params = {}

            if 'download_folder' in self.__prefs:
                d = pathlib.Path(self.__prefs['download_folder']).resolve()

                if d.exists() and d.is_dir():
                    d = d / sel
                    params['saveto'] = str(d)

            self.__client.getfile(path, **params)

    def __single_task_buttons_update(self, task=None):
        if task != None:
            if task in self.__dl_tasks:
                task = self.__dl_tasks[task]
            else: return

        if task == None or task['done']:
            self.__disable_widget(self.__tasklist_pauseone_button)
            self.__disable_widget(self.__tasklist_resumeone_button)
            self.__disable_widget(self.__tasklist_cancelone_button)

        elif task['paused']:
            self.__disable_widget(self.__tasklist_pauseone_button)
            self.__enable_widget(self.__tasklist_resumeone_button)
            self.__enable_widget(self.__tasklist_cancelone_button)

        else:
            self.__enable_widget(self.__tasklist_pauseone_button)
            self.__disable_widget(self.__tasklist_resumeone_button)
            self.__enable_widget(self.__tasklist_cancelone_button)

    def __all_tasks_buttons_update(self):
        paused, resumed, done = False, False, False

        for task in self.__dl_tasks:
            if self.__dl_tasks[task]['done']: done = True
            elif self.__dl_tasks[task]['paused']: paused = True
            else: resumed = True

        if paused: self.__enable_widget(self.__tasklist_resumeall_button)
        else: self.__disable_widget(self.__tasklist_resumeall_button)

        if resumed: self.__enable_widget(self.__tasklist_pauseall_button)
        else: self.__disable_widget(self.__tasklist_pauseall_button)

        if done: self.__enable_widget(self.__tasklist_clearcomplete_button)
        else: self.__disable_widget(self.__tasklist_clearcomplete_button)

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

    def __shortensize(self, size):
        unit = 'B'

        if size >= 1024:
            size /= 1024
            unit = 'KB'

        if size >= 1024:
            size /= 1024
            unit = 'MB'

        if size >= 1024:
            size /= 1024
            unit = 'GB'

        return str('%.2f' % round(size, 2)) + ' ' + unit

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
            rate = self.__shortensize(rate) +'/s'
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

    def __pref_menu(self):
        self.__pref_window = tk.Toplevel(self.__tk)
        self.__pref_window.title('Preferences')
        self.__pref_window.transient(self.__tk)

        destlabel = ttk.Label(self.__pref_window, text='Download to:')
        destlabel.grid(row=1, column=1, padx=8, pady=8)

        self.__pref_download_dest_text = ttk.Entry(self.__pref_window)
        self.__pref_download_dest_text.grid(
            row=1, column=2, columnspan=2, padx=(0,8), pady=8
        )

        if 'download_folder' in self.__prefs:
            dest = self.__prefs['download_folder']

        else: dest = 'Application Folder'

        self.__pref_download_dest_text.insert(0, dest)

        self.__pref_download_dest_button = ttk.Button(
            self.__pref_window, text='Browse',
            command=self.__pref_menu_download_dest_select
        )

        self.__pref_download_dest_button.grid(
            row=1, column=4, pady=8, padx=(0,8)
        )

        self.__pref_ok_button = ttk.Button(
            self.__pref_window, text='Ok', command=self.__pref_ok
        )

        self.__pref_ok_button.grid(
            row=2, column=3, padx=8, pady=(0,8), sticky=tk.E
        )

        self.__pref_cancel_button = ttk.Button(
            self.__pref_window, text='Cancel',
            command=self.__pref_window.destroy
        )

        self.__pref_cancel_button.grid(
            row=2, column=4, padx=(0,8), pady=(0,8), sticky=tk.W
        )

    def __about_menu(self):
        about_box = AboutBox(self.__tk)

    def __pref_menu_download_dest_select(self):
        dir = tk_filedialog.askdirectory()
        if type(dir) == str and len(dir) != 0:
            text = self.__pref_download_dest_text.get() #TODO: Improve
            self.__pref_download_dest_text.delete(0, len(text))
            self.__pref_download_dest_text.insert(0, dir)

    def __pref_download_dest_set(self, dest=''):
        if dest != 'Application Folder' and dest != '':
            p = pathlib.Path(dest)

            if p.exists() and p.is_dir():
                self.__prefs['download_folder'] = dest
                return True

        return False

    def __pref_ok(self):
        dest = self.__pref_download_dest_text.get().strip()
        self.__pref_download_dest_set(dest)

        self.__prefs_save()
        self.__pref_window.destroy()

    def __prefs_load(self):
        self.__prefs = {}

        try: prefs = open('prefs', 'rt')
        except: return False

        for ln in prefs:
            try: self.__prefs[ln[: ln.index('=')]] = ln[ln.index('=') + 1 : -1]
            except: pass

        prefs.close()
        return True

    def __prefs_save(self):
        try: prefs = open('prefs', 'wt')
        except: return False

        for k in self.__prefs: prefs.write(k + '=' + self.__prefs[k] + '\n')

        prefs.close()
        return True

    def __start_server(self): pass

    def __stop_server(self): pass

    def __disconnect(self, forquit=False):
        if self.__client != None:
            client = self.__client
            self.__client = None

            client.getfile_pause()
            client.cleanup()

            self.__tasklist_current_selection = None
            self.__dl_tasks = []
            self.__listings = []
            self.__listings_forward = []

            self.__display_listing()

            for child in self.__tasklist.get_children():
                self.__tasklist.delete(child)

            self.__single_task_buttons_update()
            self.__all_tasks_buttons_update()

            if not forquit: self.__filelist_address_bar_state('go')

    def __exit(self):
        if not self.__exit_in_progress:
            self.__exit_in_progress = True
            self.__disconnect(forquit=True)
            self.__tk.destroy()

if __name__ == '__main__':
    app = Application()
    app.start()
