# MPV-VJ2 Copyright 2016 paulguy <paulguy119@gmail.com>
#
# This file is part of MPV-VJ2.
#
# MPV-VJ2 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MPV-VJ2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MPV-VJ2.  If not, see <http://www.gnu.org/licenses/>.


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
import time
import json

import MainWindow
import JSONSocket
import MPVVJState
import Logger

# TODO
# new/save/load (and server) - DONE
# file browsing (and server) - DONE
# manipulate loop/random playback - DONE
# manipulate "played" state - DONE
# unset all played in playlist (and server)
# only show filenames without paths in playlist views - DONE
# playlist organization with drag and drop (and server)
# tooltips
# save / save as
# fix 'played' logic
# bugs and crashes

TPS = 20


class MPVVJClient:
  CONNECT_TIMEOUT = 30
  DEFAULT_HOST = "127.0.0.1"
  DEFAULT_PORT = "12345"
  KEEPALIVE_PERIOD = 30
  TIMEOUT_PERIOD = 45
  
  def __init__(self):
    self.win = None
    self.state = None
    self.socket = None
    self.fd = None
    self.logger = Logger.Logger()
    self.settings = { # options should be initialized as strings
      'host': MPVVJClient.DEFAULT_HOST,
      'port': MPVVJClient.DEFAULT_PORT,
    }

  def setWindow(self, win):
    self.win = win
    self.logger.setWindow(self.win.logView)

  def sendResponse(self, responseType, value, args=None):
    if(args == None):
      args = {responseType: value}
    else:
      if(type(args) != dict):
        raise TypeError
      args.update({responseType: value})
    
    if(self.socket != None):
      if(self.socket.connected == True):
        self.logger.log("server <-- " + repr(args))
      else:
        self.logger.log("buffer <-- " + repr(args))
      try:
        self.socket.sendObjAsJSON(args)
        self.connectTime = time.monotonic()
      except ConnectionRefusedError:
        self.logger.log("Connection refused.")
        self.disconnect()
      except BrokenPipeError:
        self.logger.log("Broken pipe, connection dropped.")
        self.disconnect()
    else:
      self.logger.log("nobody <-- " + repr(args))

  def sendCommand(self, command, args=None):
    self.sendResponse('command', command, args)

  def requestAllState(self):
    self.sendCommand('get-all-state')

  def sendKeepalive(self):
    self.sendCommand('keep-alive')

  def sendDisconnect(self):
    self.sendCommand('disconnect')

  def connect(self):
    port = None
    try:
      port = int(self.settings['port'])
    except ValueError:
      self.logger.log("'port' isn't an integer.")
      return
    if(port < 1 or port > 65535):
      self.logger.log("'port' must be between 1 and 65535.")
      return
    if(self.socket != None):
      self.logger.log("Already connected.")
      return
    self.logger.log("Connecting...")
    try:
      self.socket = JSONSocket.JSONTCPSocket(listening=False, host=self.settings['host'], port=port)
    except ConnectionError as e:
      self.logger.log("Connection failed: " + e.args[0])
      self.disconnect()
      return
    self.connectTime = time.monotonic()
    self.lastAct = time.monotonic()
    self.requestAllState()

  def disconnect(self):
    if(self.socket != None):
      if(self.socket.connected == True):
        self.sendDisconnect()
      self.socket.close()
      self.socket = None
      if(self.state != None):
        self.logger.log("Disconnected.")
      else:
        self.logger.log("Connection canceled.")
    self.state = None
    self.win.clientDisconnected()

  def newPlaylist(self, name):
    self.sendCommand('new-playlists', {'playlists': [{'name': name}]})

  def addEntries(self, playlist, entries):
    nameList = []
    for entry in entries:
      nameList.append({'name': entry})
    self.sendCommand('add-entries', {'playlist': playlist, 'entries': nameList})

  def cuePlaylist(self, playlist):
    self.sendCommand('cue-playlist', {'playlist': playlist})

  def cueEntry(self, playlist, idx):
    self.sendCommand('cue-item', {'playlist': playlist, 'item': idx})

  def deletePlaylists(self, playlists):
    self.sendCommand('delete-playlists', {'playlists': playlists})

  def deleteEntries(self, playlist, entries):
    self.sendCommand('delete-entries', {'playlist': playlist, 'entries': entries})

  def startMPV(self):
    self.sendCommand('run-mpv')

  def stopMPV(self):
    self.sendCommand('terminate-mpv')

  def playMedia(self):
    self.sendCommand('play')

  def stopMedia(self):
    self.sendCommand('stop')

  def getPlaylistEntries(self, playlist):
    pl = self.state.findPlaylistByName(playlist)
    return(pl[1].currentCue, pl[1].getEntries())

  def getOpts(self):
    return(self.state.mpvopts)

  def sendOpts(self):
    self.sendCommand('set-mpv-opts', {'opts': self.state.mpvopts})

  def newSession(self):
    self.sendCommand('clear-all')

  def togglePlayed(self, playlist, idx):
    self.sendCommand('set-played', {'playlist': playlist, 'item': idx})

  def toggleRandom(self, playlist):
    self.sendCommand('set-random', {'playlist': playlist})

  def toggleLooping(self, playlist):
    self.sendCommand('set-looping', {'playlist': playlist})

  def saveObjAsJSON(self, fd, obj):
    fd.write((json.dumps(obj) + "\n"))

  def saveResponse(self, fd, responseType, value, args=None):
    if(args == None):
      args = {responseType: value}
    else:
      if(type(args) != dict):
        raise TypeError
      args.update({responseType: value})
    
    self.logger.log("file <-- " + repr(args))
    self.saveObjAsJSON(fd, args)

  def saveCommand(self, fd, event, args=None):
    self.saveResponse(fd, 'command', event, args)

  def savePlaylists(self, fd):
    self.saveCommand(fd, 'new-playlists', {'playlists': self.state.getPlaylists()})

  def savePlaylist(self, fd, pl):
    self.saveCommand(fd, 'add-entries', {'playlist': pl.name, 'entries': pl.getEntries()})
    self.saveCommand(fd, 'cue-item', {'playlist': pl.name, 'item': pl.currentCue})

  def saveMpvOpts(self, fd):
    self.saveCommand(fd, 'set-mpv-opts', {'opts': self.state.mpvopts})

  def saveCuePlaylist(self, fd, name):
    self.saveCommand(fd, 'cue-playlist', {'playlist': name})

  def saveFile(self, filename):
    with open(filename, 'w') as fd:
      self.savePlaylists(fd)
      for pl in self.state.playlists:
        if(len(pl.entries) != 0):
          self.savePlaylist(fd, pl)
      self.saveMpvOpts(fd)

      current = self.state.getCurrent()
      if(current != None):
        self.saveCuePlaylist(fd, current[0])

  def loadFile(self, filename):
    self.newSession()
    self.fd = open(filename, 'r')

  def getFileList(self, path, playlist):
    self.sendCommand('list-files', {'path': path, 'playlist': playlist})

  def tick(self, nothing):
    if(self.socket != None):
      obj = self.socket.getJSONAsObj()
      if(obj == None):
        if(self.state == None):
          if(time.monotonic() - self.connectTime > MPVVJClient.CONNECT_TIMEOUT):
            self.logger.log("Connection failed.")
            self.disconnect()
        else:
          if(time.monotonic() - self.connectTime > MPVVJClient.KEEPALIVE_PERIOD):
            self.sendKeepalive()
            self.connectTime = time.monotonic()
          if(time.monotonic() - self.lastAct > MPVVJClient.TIMEOUT_PERIOD):
            self.logger.log("Connection timed out.")
            self.disconnect()
      else:
        self.lastAct = time.monotonic()
        if(self.state == None):
          self.state = MPVVJState.MPVVJState()
          self.win.clientConnected()
          self.logger.log("Connection established.")
        self.logger.log("server --> " + repr(obj))

        if(self.fd != None):
          def readFunc():
            line = self.fd.readline()
            if(line == ""):
              self.fd.close()
              self.fd = None
              return
            self.logger.log("file --> " + line)
            try:
              obj = json.loads(line)
            except json.decoder.JSONDecodeError as e:
              self.logger.log("Bad JSON: " + e.args[0])
              self.fd.close()
              self.fd = None
              return
            if('command' not in obj):
              self.logger.log("No 'command'.")
              self.fd.close()
              self.fd = None
              return
            cmd = obj['command']
            del obj['command']
            self.sendCommand(cmd, obj)
          readFunc()

        if('event' in obj):
          if(obj['event'] == 'new-playlists'):
            event = obj['event']
            del obj['event']
            ret = self.state.newPlaylists(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.newPlaylists(obj)
          elif(obj['event'] == 'delete-playlists'):
            event = obj['event']
            del obj['event']
            ret = self.state.deletePlaylists(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.deletePlaylists(obj)
          elif(obj['event'] == 'add-entries'):
            event = obj['event']
            del obj['event']
            ret = self.state.addEntries(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.addEntries(obj)
          elif(obj['event'] == 'delete-entries'):
            event = obj['event']
            del obj['event']
            ret = self.state.deleteEntries(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.deleteEntries(obj)
          elif(obj['event'] == 'cue-playlist'):
            event = obj['event']
            del obj['event']
            ret = self.state.setCurrentPlaylist(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.setCurrentPlaylist(obj)
          elif(obj['event'] == 'cue-item'):
            event = obj['event']
            del obj['event']
            ret = self.state.setPlaylistCurrentEntry(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.cueItem(obj)
          elif(obj['event'] == 'clear-all'):
            event = obj['event']
            del obj['event']
            self.state = MPVVJState.MPVVJState()
            self.win.clearState()
          elif(obj['event'] == 'set-random'):
            event = obj['event']
            del obj['event']
            ret = self.state.setPlaylistRandom(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.setRandom(obj)
          elif(obj['event'] == 'set-looping'):
            event = obj['event']
            del obj['event']
            ret = self.state.setPlaylistLooping(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.setLooping(obj)
          elif(obj['event'] == 'set-played'):
            event = obj['event']
            del obj['event']
            ret = self.state.setPlaylistLooping(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.win.setPlayed(obj)
          elif(obj['event'] == 'keep-alive'):
            pass
          elif(obj['event'] == 'mpv-started'):
            self.win.MPVStarted()
          elif(obj['event'] == 'mpv-terminated' or obj['event'] == 'mpv-unexpected-termination'):
            self.win.MPVStopped()
          elif(obj['event'] == 'playing'): #ugly hack to make sure cue display is synced
            event = obj['event']
            del obj['event']
            ret = self.state.setPlaylistCurrentEntry(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)
            else:
              self.state.setCurrentPlaylist(obj)
              self.state.advance()
              current = self.state.getCurrent()
              if(current == None):
                self.win.setCurrentPlaylist({'playlist': None})
                self.win.cueItem({'playlist': None, 'item': None})
              else:
                self.win.setCurrentPlaylist({'playlist': current[0]})
                self.win.cueItem({'playlist': current[0], 'item': current[1]})
              self.win.playing(obj)
          elif(obj['event'] == 'stopped'):
            self.win.stopped()
          elif(obj['event'] == 'set-mpv-opts'):
            event = obj['event']
            del obj['event']
            ret = self.state.setMpvOpts(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)        
            else:
              self.win.haveOpts()
          elif(obj['event'] == 'file-list'):
            event = obj['event']
            del obj['event']
            ret = self.win.listFiles(obj)
            if(ret != None):
              self.logger.log(event + ": " + ret)        
          else:
            self.logger.log("Unknown action!")
        elif('error' in obj):
          if(obj['error'] == 'failure'):
            if('message' in obj):
              self.logger.log("Server reported failure: " + obj['message'])
            else:
              self.logger.log("Server reported failure but left no message.")
          elif(obj['error'] == 'success'):
            self.logger.log("Generic success response.")
        else:
          self.logger.log("JSON statement with nothing to do!")
    return(GLib.SOURCE_CONTINUE)

if(__name__ == '__main__'):
  client = MPVVJClient()
  win = MainWindow.MainWindow(client)
  client.setWindow(win)
  win.connect("delete-event", Gtk.main_quit)
  win.show_all()
  GLib.timeout_add(1000/TPS, client.tick, client)
  Gtk.main()
  client.disconnect()
