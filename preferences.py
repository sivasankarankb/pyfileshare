import tkinter as tk
import tkinter.filedialog as tk_filedialog
from tkinter import ttk

import pathlib

class Preferences:
    def __init__(self, path='prefs'):
        self.__path = path

    def load(self):
        self.__prefs = {}

        try: prefs = open(self.__path, 'rt')
        except: return False

        for ln in prefs:
            try: self.__prefs[ln[: ln.index('=')]] = ln[ln.index('=') + 1 : -1]
            except: pass

        prefs.close()
        return True

    def save(self):
        try: prefs = open(self.__path, 'wt')
        except: return False

        for k in self.__prefs: prefs.write(k + '=' + self.__prefs[k] + '\n')

        prefs.close()
        return True

    def set_download_dest(self, dest):
        self.__prefs['download_folder'] = dest

    def get_download_dest(self):
        try: return self.__prefs['download_folder']
        except KeyError: pass

prefs_instance = None

def get_instance():
    global prefs_instance

    if prefs_instance == None: prefs_instance = Preferences()
    
    return prefs_instance

class PreferencesWindow:
    def __init__(self, master, prefs):
        self.__prefs = prefs

        self.__window = tk.Toplevel(master)
        self.__window.title('Preferences')
        self.__window.transient(master)

        destlabel = ttk.Label(self.__window, text='Download to:')
        destlabel.grid(row=1, column=1, padx=8, pady=8)

        self.__pref_download_dest_text = ttk.Entry(self.__window)
        self.__pref_download_dest_text.grid(
            row=1, column=2, columnspan=2, padx=(0,8), pady=8
        )

        dest = self.__prefs.get_download_dest()

        if dest == None: dest = 'Application Folder'

        self.__pref_download_dest_text.insert(0, dest)

        self.__pref_download_dest_button = ttk.Button(
            self.__window, text='Browse',
            command=self.__pref_menu_download_dest_select
        )

        self.__pref_download_dest_button.grid(
            row=1, column=4, pady=8, padx=(0,8)
        )

        self.__pref_ok_button = ttk.Button(
            self.__window, text='Ok', command=self.__pref_ok
        )

        self.__pref_ok_button.grid(
            row=2, column=3, padx=8, pady=(0,8), sticky=tk.E
        )

        self.__pref_cancel_button = ttk.Button(
            self.__window, text='Cancel',
            command=self.__window.destroy
        )

        self.__pref_cancel_button.grid(
            row=2, column=4, padx=(0,8), pady=(0,8), sticky=tk.W
        )

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
                self.__prefs.set_download_dest(dest)
                return True

        return False

    def __pref_ok(self):
        dest = self.__pref_download_dest_text.get().strip()
        self.__pref_download_dest_set(dest)

        self.__prefs.save()
        self.__window.destroy()