#!/usr/bin/env python3

# pyfileshare Client utilities and CLI (pyfs-client.py)
# Version 0.1

# Copyright (c) 2020 Sivasankaran K B

#TODO:
# Move file download progress saving into client (save server ip as well)
# Check file hash when resuming a file after app (exit and) restart
# Add directory downloading
# Add I/O layering for compression and encryption
# Option for hash check disable (TCP/IP already does this right?)
# Move download manager process management into it's class
# Split download manager into functions
# Add a monitor thread and instant response pipe to download manager process
# Chunk size changing and dynamic calculation
# Multiple servers at a time support
# Better handling of failed network accesses (timeouts, retries)
# Auto detect local network pyfs servers
# Evaluate what methods and fields need to stay private
# Documentation - comments and docstrings

import math
import io
import time

import hashlib
import pathlib
import shelve

import threading
import multiprocessing as mp

import requests

server_addr = 'http://127.0.0.1:8080'
progress_storage = 'progress.shelf'

class ClientLogic:
    def get_json_from(self, path='', params=None, bypass=False):
        if not self.__server_ok and not bypass: return None

        try: request = requests.get(self.__server_addr + path, params = params)
        except: return None

        if request.status_code != requests.codes.ok: return None

        try: response = request.json()
        except ValueError: return None

        return  response

    def get_bytes_from(self, path='', params=None, bypass=False):
        if not self.__server_ok and not bypass: return None

        try: request = requests.get(self.__server_addr + path, params = params)
        except: return None

        if request.status_code != requests.codes.ok: return None

        return  request.content

    def __init__(self, addr):
        self.__server_addr = addr
        self.__server_ok = False

        response = self.get_json_from(bypass=True)

        if response == None: return
        if 'application' not in response: return
        if response['application'] != 'pyfs': return

        self.__server_ok = True
        self.__server_name = response['servername']
        self.__server_chunkdefault = response['chunkdefault']

    def server_ok(self): return self.__server_ok

    def server_name(self):
        if self.__server_ok: return self.__server_name

    def server_chunkdefault(self):
        if self.__server_ok: return self.__server_chunkdefault

    def list(self, path=''): return self.get_json_from('/list/' + path)

    def gethash(self, from_, part=None, chunksize = None):

        if type(from_) == type(b'b'):
            hash = hashlib.sha256()
            hash.update(from_)
            return hash.hexdigest()

        try:
            params = {'part': int(part)}
            if chunksize != None: params['chunksize'] = int(chunksize)

        except ValueError: return None

        hash = self.get_json_from('/hash/' + from_, params=params)

        if hash == None: return None
        if hash['status'] != 'ok': return None
        if 'sha256' in hash: return hash['sha256']

class DownloadManager(ClientLogic):
    def __init__(self, addr, progress_storage):
        ClientLogic.__init__(self, addr)
        self.__progress_storage = progress_storage

    def getfile_proc_fun(self, pipe):
        tasks = []
        active_task_count = 0

        try: progress = shelve.open(self.__progress_storage, flag='r')
        except: progress = None

        if progress != None and 'getfile_tasks' in progress:
            tasks = progress['getfile_tasks']

            for task in tasks:
                if task['done']: continue

                try: file = open(task['saveto'], 'r+b')
                except OSError: file = None

                if file != None:
                    file.seek(0, io.SEEK_END) # Seek to end of file
                    task['file'] = file
                    task['lasttime'] = time.monotonic()

                    partdone = task['nextpart']
                    if partdone > 0: partdone -= 1

                    if task['paused']: status = 'filepaused'

                    else:
                        status = 'fileresumed'
                        active_task_count += 1

                    pipe.send({
                        'status': status,
                        'name': task['listing']['info']['name'],
                        'path': task['listing']['info']['path'],
                        'partdone': partdone, 'partmax': task['maxparts']
                    })

        if progress != None: progress.close()

        while True:
            if active_task_count > 0: data_available = pipe.poll()
            else: data_available = pipe.poll(None) # Blocking wait

            if data_available: data = pipe.recv()
            else: data = None

            if type(data) == type({}) and 'command' in data:
                if data['command'] == 'stop': break

                elif data['command'] == 'file':
                    succeed = False
                    listing = self.list(data['path'])
                    listed = listing != None and listing['status'] == 'ok'

                    if listed and listing['type'] == 'file':
                        size = listing['info']['size']
                        chunksize = self.server_chunkdefault()

                        if size == 0: maxparts = -1
                        else: maxparts = math.floor(size / chunksize)

                        if 'saveto' in data: destpath = data['saveto']
                        else: destpath = listing['info']['name']

                        destpath = str(pathlib.Path(destpath).resolve())

                        try: file = open(destpath, 'w+b')
                        except OSError: file = None

                        if file != None:
                            task = {
                                'listing': listing, 'chunksize': chunksize,
                                'nextpart': 0, 'maxparts': maxparts,
                                'file': file, 'saveto': destpath,
                                'done': False, 'paused': False,
                                'lasttime': time.monotonic()
                            }

                            tasks.append(task)
                            succeed = True

                    if succeed: pipe.send({
                        'status': 'filestarted', 'path': data['path'],
                        'name': listing['info']['name']
                    })

                    else: pipe.send({
                        'status': 'fileerror', 'path': data['path']
                    })

                elif data['command'] == 'pause' or data['command'] == 'resume':
                    if data['command'] == 'pause': paused = True
                    else: paused = False

                    for task in tasks:
                        if 'target' in data:
                            path = task['listing']['info']['path']
                            matches = path == data['target']

                        else: matches = True

                        if not (task['done'] or task['paused'] == paused) and matches:
                            task['paused'] = paused

                            if not paused:
                                task['lasttime'] = time.monotonic()

                            pipe.send({
                                'status': 'file' + data['command'] + 'd',
                                'path': task['listing']['info']['path'],
                                'partdone': task['nextpart'],
                                'partmax': task['maxparts']
                            })

                elif data['command'] == 'cancel' and 'target' in data:
                    tasksleft = []

                    for task in tasks:
                        path = task['listing']['info']['path']

                        if data['target'] == path and not task['done']:
                            task['file'].close()
                            dest = task['saveto']
                            pathlib.Path(dest).unlink(missing_ok=True)

                            pipe.send({
                                'status': 'filecanceled', 'path': path
                            })

                        else: tasksleft.append(task)

                    tasks = tasksleft

            active_task_count = 0

            for task in tasks:
                if task['paused']: continue

                if task['nextpart'] > task['maxparts']:
                    task['file'].close()
                    task['done'] = True

                else: active_task_count += 1

                params = {
                    'part': task['nextpart'], 'chunksize': task['chunksize']
                }

                path = task['listing']['info']['path']
                timestart = time.monotonic()

                data = self.get_bytes_from('/get/' + path, params=params)
                if data == None: continue

                hash = self.gethash(path, params['part'])
                if hash == None or hash != self.gethash(data): continue

                task['file'].write(data)
                timeend = time.monotonic()
                timetaken = timeend - task['lasttime']
                task['lasttime'] = timeend

                pipe.send({
                    'status': 'fileprogress', 'path': path,
                    'partdone': task['nextpart'], 'partmax': task['maxparts'],
                    'partsize': len(data) + len(hash), 'timetaken': timetaken
                })

                task['nextpart'] += 1

            tasksleft = []
            index = 0

            for task in tasks:
                if not task['done']: tasksleft.append(task)

                else: pipe.send({
                    'status': 'filedone',
                    'path': task['listing']['info']['path']
                })

                index += 1

            tasks = tasksleft

        for task in tasks:
            if not task['done']: task['file'].close()
            del task['file']
            del task['lasttime']

        if len(tasks) > 0:
            try: progress = shelve.open(self.__progress_storage)
            except: progress = None

            if progress != None:
                progress['getfile_tasks'] = tasks
                progress.close()

        else: pathlib.Path(self.__progress_storage).unlink(missing_ok=True)

class PyFSClient(ClientLogic):
    def __init__(self, addr, progress_storage):
        ClientLogic.__init__(self, addr)

        if not self.server_ok(): return

        dm = DownloadManager(addr, progress_storage)

        self.__getfile_pipe, childpipe = mp.Pipe()
        self.__getfile_pipe_lock = threading.Lock()

        process = mp.Process(target=dm.getfile_proc_fun, args=(childpipe,))
        process.start()
        self.__getfile_process = process

        thread = threading.Thread(target=self.__getfile_monitor)
        self.__getfile_monitor_thread_stop = False
        self.__getfile_monitor_thread = thread
        self.__getfile_monitor_thread.start()

    def __getfile_monitor(self):
        self.__getfile_monitor_callback = None
        self.__getfile_monitor_thread_stop = False

        while not self.__getfile_monitor_thread_stop:
            try:
                self.__getfile_pipe_lock.acquire()

                if self.__getfile_pipe.poll():
                    data = self.__getfile_pipe.recv()
                else: data = None

                self.__getfile_pipe_lock.release()

                if data == None: time.sleep(0.1) # Go idle
                else: time.sleep(0.02)

            except:
                self.__getfile_pipe_lock.release()
                break

            if data != None and type(data) == type({}):
                callback = self.__getfile_monitor_callback

                if callback != None: callback(data)

                else:
                    if 'status' in data:
                        if data['status'] == 'filestarted':
                            print('Started downloading', data['path'])

                        elif data['status'] == 'fileerror':
                            print('Failed to download', data['path'])

                        elif data['status'] == 'filedone':
                            print('Finished downloading', data['path'])

                        elif data['status'] == 'filepaused':
                            print('Paused downloading', data['path'])

                        elif data['status'] == 'fileresumed':
                            print('Resumed downloading', data['path'])

                        elif data['status'] == 'fileprogress':
                            print('Downloading', data['path'])

                            numerator = data['partdone'] + 1
                            denominator = data['partmax'] + 1
                            percent = math.floor(100 * numerator/ denominator)

                            rate = data['partsize'] / data['timetaken']
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

                            print(str(percent) + '% complete at', rate)

    def getfile_monitor_silence(self, callback):
        self.__getfile_monitor_callback = callback

    def __getfile_monitor_stop(self):
        self.__getfile_monitor_thread_stop = True
        self.__getfile_monitor_thread.join()

    def getfile(self, path, callback=None):
        self.__getfile_pipe_lock.acquire()
        self.__getfile_pipe.send({'command': 'file', 'path': path})
        self.__getfile_pipe_lock.release()

    def getfile_pause(self, target=None):
        self.__getfile_pipe_lock.acquire()
        if target == None: self.__getfile_pipe.send({'command': 'pause'})
        else: self.__getfile_pipe.send({'command': 'pause', 'target': target})
        self.__getfile_pipe_lock.release()

    def getfile_resume(self, target=None):
        self.__getfile_pipe_lock.acquire()
        if target == None: self.__getfile_pipe.send({'command': 'resume'})
        else: self.__getfile_pipe.send({'command': 'resume', 'target': target})
        self.__getfile_pipe_lock.release()

    def getfile_cancel(self, target):
        self.__getfile_pipe_lock.acquire()
        self.__getfile_pipe.send({'command': 'cancel', 'target': target})
        self.__getfile_pipe_lock.release()

    def cleanup(self):
        if self.__getfile_process.is_alive():
            self.__getfile_pipe_lock.acquire()
            self.__getfile_pipe.send({'command': 'stop'})
            self.__getfile_pipe_lock.release()

        self.__getfile_monitor_stop()

        for unused in range(6):
            if self.__getfile_process.is_alive(): time.sleep(0.5)
            else: break

        if self.__getfile_process.is_alive():
            self.__getfile_process.terminate()

            for unused in range(4):
                if self.__getfile_process.is_alive(): time.sleep(0.5)
                else: break

            if self.__getfile_process.is_alive(): self.__getfile_process.kill()

def pyfs_client_cli(logic):
    if logic.server_ok():
        shares = logic.list()
        listings = [shares]
        server_name = logic.server_name()

        while True:
            if len(listings) > 1: dir = ' ' + listings[-1]['info']['name']
            else: dir = ''

            prompt = '[' + server_name + dir + ']' + '$ '
            command = input(prompt)

            if command == 'help':
                print(
                    ' list Shows the content of current directory.\n'+
                    ' open Go inside a directory.\n'+
                    ' back Go back to previous directory.\n'+
                    ' get  Download a file in the current directory.\n'+
                    ' quit Exit the application.'
                )

            elif command == 'list':
                listing = logic.list(listings[-1]['info']['path']) # Refresh

                if listing != None and listing['status'] == 'ok':
                    listings[-1] = listing

                if 'dirs' in listings[-1]['info']:
                    for dir in listings[-1]['info']['dirs']: print(dir + '/')
                if 'files' in listings[-1]['info']:
                    for file in listings[-1]['info']['files']: print(file)

            elif command.startswith('open'):
                target = command[5:]

                if target in listings[-1]['info']['dirs']:
                    targetpath = listings[-1]['info']['path'] + target
                    response = logic.list(targetpath)

                    if response != None and response['status'] == 'ok':
                        listings.append(response)

                    else: print(' Server error. Try again.')

                else:
                    print(target, 'is not a directory.')

            elif command == 'back':
                if len(listings) > 1: listings.pop()

            elif command.startswith('get'):
                target = command[4:]

                if target in listings[-1]['info']['files']:
                    targetpath = listings[-1]['info']['path'] + target
                    logic.getfile(targetpath)

                else:
                    print(target, 'is not a file.')

            elif command == 'quit': break

            elif command != '': print(' Don\'t know how to do that. Try help.')

        logic.cleanup()

    else: print("Unable to connect.")

if __name__ == '__main__':
    logic = PyFSClient(server_addr, progress_storage)
    pyfs_client_cli(logic)
