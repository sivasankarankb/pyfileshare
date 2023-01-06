# pyfileshare
An HTTP based file sharing application written in Python.

## Concept
The `pyfileshare` concept of sharing is unrestricted, progressive reading
of files and listing of directories (folders and/or drives). The application
is divided into two main parts. The server which provides the file sharing
functionality and the client to view and download files.

Install the server on the machine from which the files are to be shared.
Then add each directory you want to share to the server's settings, giving
it a share name. Install the client on any machine from which you wish
to access the files. Enter the address of the server machine in the client
and press go.

While `pyfileshare` is best used on local networks such as your home or office,
it can be accessed from anywhere around the world, if the server port used
is forwarded by your ISP. Remember that shared files are accessible
to __everybody__ that can connect to your machine. Do not put private files
in shared locations.

Currently, file transfers are __insecure__. No encryption is used. Anybody
that can see your network traffic can grab the content of the transferred
files. __Strong encryption__ will be added in the near future.

## Installation
To try pyfileshare:

1. Get a copy from the
   [releases](https://github.com/sivasankarankb/pyfileshare/releases) page.
   
2. Extract the code where ever you want.

3. Install [Python 3.x](https://www.python.org) if you're on Windows or macOS.
   Windows users must enable the _Add Python to PATH_ setup option.

4. Install the additional requirements with python's `pip`.
   Open a terminal (Command Prompt or PowerShell on Windows) and type in
   the following commands. You may need administrative previleges.

   Use `pip3` instead of `pip` on Linux as both Python 2 and 3
   are usually pre-installed.

   Client requirements: `pip install requests`.

   Server requirements: `pip install bottle cherrypy`.

__Note__: I cannot verify the application's working on MacOS as I don't have
access to an Apple machine. But the Linux instructions should work for Mac.
Don't forget to install the latest Python 3 from the Python website.

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

Suppose you want to share the E Drive and your Downloads folder:

```python
shares = {
    'e_drive': 'E:\\',
    'downloads': 'C:\\Users\\Me\\Downloads\\'
}
```

Note the __double backslashes__ used inside the paths.

Edit the name of the server by changing the `server_name` line.
This is not of any particular use as of now, though. To change the IP address
and port number that the server listens on, go to the end of the file
and change the `server.socket_host` and the `server.socket_port` lines.

The server listens on all interfaces (e.g. Ethernet (LAN), WiFi, Bluetooth)
by default. You can change this by setting the IP address to that of
the interface you want to listen to. The port used is `8080` by default.

If you don't understand these, just leave them as is.

## Running the server
Double click `pyfs-server.py` on Windows. Run `./pyfs-server.py` or
`python3 pyfs-server.py` from inside the application directory
in a terminal on Linux.

## Running the client
Finally, we are here. Just double click `pyfs-gui.py` on Windows.
On a Linux distro, open a terminal window and point it to the app directory.
Then run `./pyfs-gui.py` or `python3 pyfs-gui.py`.

Type in the IP address and port of the server machine. The address format
is `http://ipaddress:portnumber`. The default port is `8080`. Double click
on a file to download it to the pyfileshare directory. Saving files to other
places will be implemented in the near future.

For those of you who don't know what an IP address is, it looks like this:
`192.168.1.110` - a sequence of four numbers, separated by dots. To get
the IP address of a machine, check the properties of your network device
or use `ipconfig` in a PowerShell or Command Prompt on Windows.
Look for the lines that say `IPv4 Address`.

Run `ip address`, `sudo ifconfig` or look in the network or connection
information on Linux. If you're using the Linux command line tools, look
for the lines that say `inet`.
