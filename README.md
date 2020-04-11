# pyfileshare
An HTTP based file sharing application written in Python.

## Concept
The `pyfileshare` concept of sharing is unrestricted, progressive reading
of files and listing of directories (folders and/or drives).

The application is divided into two main parts. The server which provides
the file sharing functionality and the client to view and download files.

You simply add each directory you want to share to the server's settings,
giving it a share name. Enter the address of the server in the client
and press go.

## Installation
First install a recent version of Python 3 from https://python.org.
If you're on a GNU/Linux distro, you probably already have Python.
Windows users must make sure to enable the _Add Python to PATH_ setup option.

Secondly, install the additional requirements with python's `pip`.
Open a terminal (Command Prompt or PowerShell on Windows) and type in
the following commands. You may need administrative previleges.

Use `pip3` instead of `pip` on Linux as both Python 2 and 3
are usually pre-installed.

Client requirements: `pip install requests`.

Server requirements: `pip install bottle cherrypy`.

Lastly, either clone this repository with `git clone repository_url`
or download a ZIP file (especially useful if you are on Windows) to get
the application files. Get the repository URL or ZIP file from the green
clone button above. Extract the ZIP file where ever you want.

## Setting up file sharing
Sharing is done by allowing access to a directory on the computer.
Open the `pyfs-server.py` file. This contains code of the server.
Edit the line that says `shares = { ... }`.

__Linux (Unix) sharing examples:__

Suppose you want to add `/home/user/` with the share name `yuser`:

```python
shares = {'yuser': '/home/user/'}
```

Let's add `/var/www/html` under the name `mirror` to this:

```python
shares = {
     'yuser': '/home/user/',
     'mirror': '/var/www/html/'
}
```

__Windows sharing example:__

Suppose you want to the E Drive and your Downloads folder:

```python
shares = {
    'e_drive': 'E:\\',
    'downloads': 'C:\\Users\\Me\\Downloads\\'
}
```

Note the __double backslashes__ used inside the paths.

Edit the name of the server by changing the `server_name` line.
This not of any particular use as of now, though.

To change the IP address andport number that the server listens on,
go to the end of the file and change the `server.socket_host` and
the `server.socket_port` lines.

The server listens on all interfaces (e.g. Ethernet [LAN], WiFi, Bluetooth)
by default. You can change this by setting the IP address to that of
the interface you want to listen to.

The port used is `8080` by default. You will need administrative previleges
to use a port less than or equal to `1024`.

If you don't understand these, just leave them as is.

## Running the server
Double click `pyfs-server.py` on Windows. Run `python3 pyfs-server.py`
from inside the application directory in a terminal on Linux.

## Running the client
Finally, we are here. Just double click `pyfs-gui.py` on Windows.
On a Linux distro, open a terminal window and point it to the app directory.
Then run `python3 pyfs-gui.py`.

Type in the IP address and port of the server machine. The address format
is `http://ipaddress:portnumber`. The default port is `8080`. Double click
on a file to download it to the pyfileshare directory. Saving files to other
places will be implemented in the near future.

To get the IP address of a machine, check the properties of your network
device or use `ipconfig` in a PowerShell or Command Prompt on Windows.

Run `ip address`, `sudo ifconfig` or look in the network or connection
information on Linux. If you're using the Linux command line tools, look
for the line that says `inet`.
