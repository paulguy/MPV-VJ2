MPV-VJ 2

MPV-VJ 2 is a program for managing multiple playlists and controlling playlist
playback using a GUI.  It has 2 components, a server (MPVVJServer) and the GUI
client program (MPVVJClient).  They communicate over TCP so control can be
established remotely.  There is no security or authentication, however, so it
shouldn't be exposed out to the internet directly.  Also, there is certainly the
possibility of remote data access.  Python 3.5 is required and a recent
PyGobject is recommended.  This program was written mostly for the intention of
controlling MPV to be captured for an online video stream, but could have other
purposes.

USAGE:
First, run the server from a directory which contains media which you want to
play, then run the client and connect to the server.  The host can be specified
under settings.  Create a playlist or multiple playlists and populate them with
media.  Start MPV then start playback.

Server Command Line Arguments:
usage: MPVVJServer.py [-h] [--mpv-path <PATH>] [--mpv-socket-path <PATH>]
                      [--bind-address <address>] [--bind-port <port>]

MPV-VJ2 - Remotely control mpv and manage playlists.

optional arguments:
  -h, --help            show this help message and exit
  --mpv-path <PATH>     Path to MPV executable.
  --mpv-socket-path <PATH>
                        Filename of socket to use for communicating with mpv.
  --bind-address <address>
                        Address to bind to.
  --bind-port <port>    Port to bind to.

Interface Overview

Top - toolbar
  new - Clear state
  load - Restore state from file
  save - Save state to file
  settings - Application settings
  connect/disconnect - Connect to/disconnect from server
  start/stop MPV - Start/stop MPV process
  MPV options - Modify options passed to MPV
  play/next - Play next cued item
  stop - Stop playback

Middle - views
  Left - Playlsits list
    Toolbar
      Add - Add a playlist
    List
      "S" - State ("C" - Cued)
      "Name" - Name
      "R" - Random play (Double click to toggle)
      "L" - Looping play (Double click to toggle)
      Keys:
        L - View selected playlist in left view
        R - View selected playlist in right view
        C - Cue selected playlist (Empty playlists can't be cued)
        DELETE - Delete selected playlists
        CTRL+F - Search
  Middle - First playlist view
    Toolbar
      Add URL - Add a URL
      Add files - Open file browser to add files
    Current playlist
    List of items
      "S" - State ("C" - Cued, "P" - Playing)
      "Name" - Name
      "P" - Played (Won't be selected for random play) (Double click to toggle)
      Keys:
        Double click - Cue this playlist and item and play immediately
        C - Cue selected item for this playlist (Won't necessarily be played
            next unless this playlist is cued as well)
        DELETE - Delete selected items
        CTRL+F - Search
  Right - Second playlist view, same as first

Bottom - log
