#!/usr/bin/env python3

# pyfileshare Server (pyfs-server.py)
# Version 0.1

# Copyright (c) 2020 Sivasankaran K B

#TODO:
# Have server return more info when listing (maybe)
# Add I/O layering for compression and encryption

import io
import time
import pathlib
import hashlib

import bottle
import cherrypy

# What paths to make available for sharing. Format is sharename: path.
shares = {'siva': '/home/siva'}

# Not partcularly useful as of yet.
server_name = 'manjodell'

file_chunk_size_default = 1024 * 1024
file_chunk_size_min = 512
file_chunk_size_max = 32 * 1024 * 1024

# -----------------------------------------------------------------------------

app = bottle.Bottle()

def time_convert(seconds):
    moment = time.localtime(seconds)
    # I liked "%A, %d %b %Y, %I:%M:%S %p %Z (UTC%z)"
    return time.strftime("%j%Y%H%M%S%z", moment)

@app.route('/')
def welcome():
    return {
       'status': 'ok', 'application': 'pyfs', 'version': 0.1,
       'chunkmax': file_chunk_size_max, 'chunkmin': file_chunk_size_min,
       'chunkdefault': file_chunk_size_default, 'servername': server_name
    }

@app.route('/list/')
def list_shares():
    keys = []
    for key in shares.keys(): keys.append(key)
    keys.sort()
    return {'status': 'ok', 'type': 'dir', 'info': {'name': '', 'path': '', 'dirs': keys}}

@app.route('/list/<sharename>')
@app.route('/list/<sharename>/')
@app.route('/list/<sharename>/<path:path>')
def list_fs(sharename, path = ''):
    if sharename not in shares:
        return {'status': 'error', 'reason': 'not exist'}

    share = pathlib.Path(shares[sharename]).resolve()
    target = share / path

    if target.exists():
        target_type = 'special'
        target_info = {}

        if target.is_file():
            target_type = 'file'
            info = target.stat()

            target_info['name'] = target.name
            target_info['path'] = sharename + '/'
            target_info['path'] += str(target.relative_to(share))

            target_info['size'] = info.st_size
            target_info['created'] = time_convert(info.st_ctime)
            target_info['modified'] = time_convert(info.st_mtime)

        elif target.is_dir():
            target_type = 'dir'
            info = target.stat()

            target_info['name'] = target.name
            target_info['path'] = sharename + '/'
            target_info['path'] += str(target.relative_to(share) / 'a')[:-1]

            target_info['created'] = time_convert(info.st_ctime)
            target_info['modified'] = time_convert(info.st_mtime)

            target_info['files'] = []
            target_info['dirs'] = []

            for child in target.iterdir():
                if child.is_dir(): target_info['dirs'].append(child.name)
                else: target_info['files'].append(child.name)

            target_info['files'].sort()
            target_info['dirs'].sort()

        return {'status': 'ok', 'type': target_type, 'info': target_info}

    else: return {'status': 'error', 'reason': 'not exist'}

# Parameters format is part=<int>[&chunksize=<int>]
@app.get('/get/<sharename>/<path:path>')
@app.get('/hash/<sharename>/<path:path>')
def read_file_part(sharename, path):
    if sharename not in shares:
        return {'status': 'error', 'reason': 'not exist'}

    target = pathlib.Path(shares[sharename]).resolve() / path

    try: part = int(bottle.request.query.part)
    except: return {'status': 'error', 'reason': 'missing part number'}

    if part < 0: return {'status': 'error', 'reason': 'negative part number'}

    try:
        chunk = int(bottle.request.query.chunksize)

        if chunk < file_chunk_size_min:
            return {'status': 'error', 'reason': 'chunk size too small'}
        elif chunk > file_chunk_size_max:
            return {'status': 'error', 'reason': 'chunk size too large'}
        else:
            chunk_size = chunk

    except:
        chunk_size = file_chunk_size_default

    if bottle.request.route.rule.startswith('/hash'): gethash = 1
    else: gethash = 0

    if target.exists():
        if target.is_file():
            handle = open(str(target), "rb")
            handle.seek(part * chunk_size, io.SEEK_SET)
            data = handle.read(chunk_size)

            if len(data) == 0:
                return {'status': 'error', 'reason': 'part number too high'}

            if gethash != 1:
                bottle.response.set_header(
                    'Content-Type', 'application/octet-stream')
                return data

            hash = hashlib.sha256()
            hash.update(data)
            return {'status': 'ok', 'sha256': hash.hexdigest()}

        else: return {'status': 'error', 'reason': 'not file'}

    else: return {'status': 'error', 'reason': 'not exist'}

cherrypy.config.update({
                           'server.socket_host': '0.0.0.0',
                           'server.socket_port': 8080
})

cherrypy.tree.graft(app, '/')

cherrypy.engine.start()
cherrypy.engine.block()
