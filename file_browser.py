import math
import time

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

def shortensize(size):
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

class FileBrowser:
    def __init__(self):
        self.__client = None
        self.__listings = []
        self.__listings_forward = []
        self.__server_addr = ''

        self.__title_listener = None
        self.__client_provider = None
        self.__connect_success_listener = None
        self.__file_downloader = None

        self.__icon_go = load_icon('icons/go.png')
        self.__icon_disconnect = load_icon('icons/disconnect.png')

        self.__icon_back = load_icon('icons/backward.png')
        self.__icon_refresh = load_icon('icons/refresh.png')
        self.__icon_forward = load_icon('icons/forward.png')

        self.__icon_file = load_icon('icons/file.png')
        self.__icon_folder = load_icon('icons/folder.png')

        self.__filesframe = ttk.Frame(master=None)

        self.__filelist_back_button = ttk.Button(
            master=self.__filesframe, text='Back',
            command=self.__filelist_back, image=self.__icon_back
        )

        self.__filelist_back_button.grid(
            row=0, column=0, sticky=tk.E, padx=(0, 8)
        )
        disable_widget(self.__filelist_back_button)

        self.__filelist_refresh_button = ttk.Button(
            master=self.__filesframe, text='Refresh',
            command=self.__filelist_refresh, image=self.__icon_refresh
        )

        self.__filelist_refresh_button.grid(row=0, column=1, padx=(0, 8))
        disable_widget(self.__filelist_refresh_button)

        self.__filelist_forward_button = ttk.Button(
            master=self.__filesframe, text='Forward',
            command=self.__filelist_forward, image=self.__icon_forward
        )

        self.__filelist_forward_button.grid(row=0, column=2, sticky=tk.W)
        disable_widget(self.__filelist_forward_button)

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

        self.__filelist = create_treeview(
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

        self.__filelist.bind('<Double-ButtonPress-1>', self.__filelist_select)

    def get_container(self): return self.__filesframe

    def connect_to(self, addr):
        if self.__client == None:
            self.__client = self.__get_client_for(addr)

        if self.__client != None:
            listing = self.__client.list()

            if listing == None:
                if not self.__client.server_ok(): self.__client = None
                self.__server_addr = ''
                return False

        else: return False

        self.__filelist_address_bar_state('disconnect')
        self.__listings = [listing]

        if not addr.endswith('/'): addr += '/'

        self.__server_addr = addr
        self.__display_listing()
        self.__handle_connect_success()

        return True

    def __display_listing(self):
        if len(self.__listings) <= 1:
            disable_widget(self.__filelist_back_button)
        else:
            enable_widget(self.__filelist_back_button)

        for child in self.__filelist.get_children():
            self.__filelist.delete(child)

        if len(self.__listings_forward) > 0:
            enable_widget(self.__filelist_forward_button)

        else: disable_widget(self.__filelist_forward_button)

        if len(self.__listings) == 0:
            disable_widget(self.__filelist_refresh_button)
            self.__set_title()
            return

        enable_widget(self.__filelist_refresh_button)

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
            self.__filelist_go_button['command'] = self.disconnect
            self.__filelist_go_button['image'] = self.__icon_disconnect
            disable_widget(self.__filelist_address_bar)

        elif state == 'go':
            self.__filelist_go_button['text'] = 'Go'
            self.__filelist_go_button['command'] = self.__filelist_go
            self.__filelist_go_button['image'] = self.__icon_go
            enable_widget(self.__filelist_address_bar)

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
                    parsedinfo['size'] = shortensize(size)

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
            self.__download_file(path, sel)

    def disconnect(self, forquit=False):
        if self.__client != None:
            client = self.__client
            self.__client = None

            client.getfile_pause()
            client.cleanup()

            self.__listings = []
            self.__listings_forward = []

            self.__display_listing()

            if not forquit: self.__filelist_address_bar_state('go')

    def set_title_listener(self, listener):
        self.__title_listener = listener

    def __set_title(self, title=''):
        if self.__title_listener != None:
            self.__title_listener(title)

    def set_client_provider(self, provider):
        self.__client_provider = provider

    def __get_client_for(self, address):
        if self.__client_provider != None:
            return self.__client_provider(address)

    def set_connect_success_listener(self, listener):
        self.__connect_success_listener = listener

    def __handle_connect_success(self):
        if self.__connect_success_listener != None:
            self.__connect_success_listener()

    def set_file_downloader(self, downloader):
        self.__file_downloader = downloader

    def __download_file(self, path, name):
        if self.__file_downloader != None:
            self.__file_downloader(path, name)
