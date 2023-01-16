#!/usr/bin/env python3

import math
import time
import statistics
import pathlib

import tkinter as tk
import tkinter.filedialog as tk_filedialog
from tkinter import ttk

from pyfs_client import PyFSClient
import pyfs_server

import file_browser
from about_box import AboutBox

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

        self.__dl_updates = []
        self.__dl_tasks = {}
        self.__tasklist_current_selection = None

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

        self.__tasksframe = ttk.Frame(master=None)

        self.__panes = ttk.PanedWindow(
            master=self.__mainframe, orient='horizontal'
        )

        self.__panes.grid(
            row=0, column=0, sticky=tk.NSEW, pady=8, padx=8
        )

        self.__mainframe.grid_rowconfigure(0, weight=1)
        self.__mainframe.grid_columnconfigure(0, weight=1)

        self.__file_browser = file_browser.FileBrowser()

        self.__file_browser.set_title_listener(self.__set_title)

        self.__file_browser.set_client_provider(self.__get_client_for)

        self.__file_browser.set_connect_success_listener(
            self.__handle_browser_connect_after
        )

        self.__file_browser.set_file_downloader(self.__download_file)

        self.__filesframe = self.__file_browser.get_container()

        self.__panes.insert('end', self.__filesframe)
        self.__panes.insert('end', self.__tasksframe)

        self.__style = ttk.Style()
        self.__style.configure('TButton', relief='solid')
        self.__style.configure('TEntry', relief='flat', padding=4)
        self.__style.configure('Treeview', rowheight=28)

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

        self.__server_menu = tk.Menu(self.__tk, tearoff=False)

        self.__server_menu.add(
            tk.COMMAND, label='Start', command=self.__start_server
        )

        self.__server_menu.add(
            tk.COMMAND, label='Stop', command=self.__stop_server,
            state=tk.DISABLED
        )

        self.__menubar.add(
            tk.CASCADE, label='Server', menu=self.__server_menu
        )
        
        help_menu = tk.Menu(self.__tk, tearoff=False)
        
        help_menu.add(
            tk.COMMAND, label='About', command=self.__about_menu
        )
        
        self.__menubar.add(
            tk.CASCADE, label='Help', menu=help_menu,
        )

        self.__tk['menu'] = self.__menubar

        self.__server = pyfs_server.get_instance()

        self.__prefs_load()

    def __set_title(self, title=''):
        if title != '': title = 'pyfileshare - ' + title
        else: title = 'pyfileshare'

        self.__tk.title(title)

    def start(self):
        self.__tk.mainloop()

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

    def __get_client_for(self, addr):
        self.__client = PyFSClient(addr, 'progress.shelf')
        self.__client.getfile_monitor_silence(self.__download_progress_pre)
        return self.__client

    def __handle_browser_connect_after(self):
        self.__client.getfile_monitor_silence(self.__download_progress)
        self.__render_silenced_updates()

    def __download_file(self, path, name):
        params = {}

        try: dest = self.__prefs['download_folder']

        except KeyError: pass

        else:
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

    def __render_silenced_updates(self):
        if len(self.__dl_updates) > 0:
            for update in self.__dl_updates:
                self.__download_progress(update)
            self.__dl_updates = []

        else:
            self.__single_task_buttons_update()
            self.__all_tasks_buttons_update()

    def __clear_tasks_list(self):
        self.__tasklist_current_selection = None
        self.__dl_tasks = []

        for child in self.__tasklist.get_children():
            self.__tasklist.delete(child)

        self.__single_task_buttons_update()
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

        try: dest = self.__prefs['download_folder']

        except KeyError: dest = 'Application Folder'

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
        self.__prefs['download_folder'] = dest

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

    def __set_server_start_state(self, state):
        if state == 'on':
            self.__server_menu.entryconfigure('Start', state=tk.DISABLED)
            self.__server_menu.entryconfigure('Stop', state=tk.NORMAL)
        elif state == 'off':
            self.__server_menu.entryconfigure('Start', state=tk.NORMAL)
            self.__server_menu.entryconfigure('Stop', state=tk.DISABLED)

    def __start_server(self):
        self.__server.start()
        self.__set_server_start_state('on')

    def __stop_server(self):
        self.__server.stop()
        self.__set_server_start_state('off')

    def __exit(self):
        if not self.__exit_in_progress:
            self.__exit_in_progress = True
            self.__file_browser.disconnect(forquit=True)
            self.__clear_tasks_list()
            self.__tk.destroy()

if __name__ == '__main__':
    app = Application()
    app.start()
