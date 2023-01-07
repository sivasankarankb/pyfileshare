# pyfileshare
An HTTP based file sharing application written in Python.

## Concept
The `pyfileshare` concept of sharing is unrestricted, progressive reading
of files and listing of directories (folders, drives). The application
is divided into two main parts. The server which provides the file sharing
functionality and the client to view and download files.

Remember that shared files are accessible to __everybody__ that can connect to
your machine. Do not put private files in shared locations.

## Installation
To try pyfileshare:

1. Get a copy from the
   [releases](https://github.com/sivasankarankb/pyfileshare/releases) page.
   
2. Extract the code wherever you want.

3. Install [Python 3.x](https://www.python.org) if you're on Windows or macOS.
   Windows users must enable the _Add Python to PATH_ setup option.

4. To keep things clean, create a
   [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)
   with `venv` and enter it.

5. Get the packages required by pyfileshare by running
   `pip3 install -r requirements.txt` inside the code directory from a terminal.

## Setting up file sharing
Sharing is done by allowing access to a directory on the computer.
Open the `pyfs-server.py` file. This contains code of the server.
Edit the line that says `shares = { ... }`.

__Linux (Unix) sharing examples:__

Suppose you want to add `/home/user/` with the share name `files`:

```python
shares = {'files': '/home/user/'}
```

Let's add `/var/www/html` under the name `mirror` to this:

```python
shares = {
     'files': '/home/user/',
     'mirror': '/var/www/html/'
}
```

__Windows sharing example:__

Suppose you want to share the E Drive and your Downloads folder:

```python
shares = {
    'e_drive': 'E:\\',
    'downloads': 'C:\\Users\\Me\\Downloads\\'
}
```

Note the __double backslashes__ used inside the paths.

## Running the server

Do `python3 pyfs-server.py`.

## Running the client

1. Do `python3 pyfs-gui.py`.

2. Type in the IP address and port of the server machine. The address format
   is `http://ipaddress:portnumber`. The default port is `8080`.

3. Double click on a file to download it to the pyfileshare directory.
