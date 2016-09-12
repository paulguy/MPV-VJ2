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


import time
import json
import random
import signal
import os
import os.path

import MPVVJState
import JSONSocket
import MPV

# TODO
# MPV options management - DONE
# new/save/load (and client) - DONE
# file browsing (and client) - DONE
# command line arguments (bind address, port, verbose logging, starting directory, ...)
# probably some more socket stuff as it comes up... - SEEMINGLY DONE!
# unset all played in playlist (and clioent)
# playlist organization (and client)
# bugs and crashes

TPS = 20


def hupHandler(signum, frame):
  print("SIGHUP received.")
  try:
    server
  except NameError:
    return
    
  if(server.socket != None):
    server.reconnectSocket()
    print("Listening socket forcibly closed and reopened")


class PlaylistStop(BaseException):
  pass


class MPVVJServer():
  PORT = 12345
  DEFAULT_MPV = "/usr/bin/mpv"
  DEFAULT_SOCKET = "/tmp/mpvsocket"
  RETRIES = 3
  TIMEOUT = 45

  def __init__(self):
    self.state = MPVVJState.MPVVJState()
    self.socket = None
    self.reconnectSocket()
    self.mpv = None
    self.connected = False
    self.playing = False
    self.path = os.getcwd()
    signal.signal(signal.SIGHUP, hupHandler)

  def reconnectSocket(self):
    if(self.socket != None):
      self.socket.close()
    self.socket = JSONSocket.JSONTCPSocket(listening=True, host=None, port=MPVVJServer.PORT)
    self.lastAct = None

  def sendResponse(self, responseType, value, args=None):
    if(args == None):
      args = {responseType: value}
    else:
      if(type(args) != dict):
        raise TypeError
      args.update({responseType: value})
    
    if(self.socket != None and self.socket.connected == True):
      print("client <-- " + repr(args))
      try:
        self.socket.sendObjAsJSON(args)
      except BrokenPipeError:
        self.reconnectSocket()
        print("Broken pipe, connection dropped.")
    else:
      print("nobody <-- " + repr(args))

  def sendStatusResponse(self, status, args=None):
    self.sendResponse('error', status, args)

  def sendEventResponse(self, event, args=None):
    self.sendResponse('event', event, args)

  def sendSuccessResponse(self, data=None):
    if(data == None):
      self.sendStatusResponse('success')
    else:
      self.sendStatusResponse('success', {'data': data})

  def sendFailureResponse(self, message=None):
    if(message == None):
      self.sendStatusResponse('failure')
    else:
      if(type(message) != str):
        raise TypeError
      self.sendStatusResponse('failure', {'message': message})

  def playCurrentAndAdvance(self):
    # since hopefully there's no other way for mpv to emit a 'start-file' event
    # we set this now so once mpv gets the event, we can tell the client which
    # item is playing.
    self.current = self.state.getCurrent()
    if(self.current == None):
      raise PlaylistStop
    self.mpv.play(self.current[2])
    self.state.advance()

  def sendPlaylists(self):
    self.sendEventResponse('new-playlists', {'playlists': self.state.getPlaylists()})

  def sendPlaylist(self, pl):
    self.sendEventResponse('add-entries', {'playlist': pl.name, 'entries': pl.getEntries()})
    self.sendEventResponse('cue-item', {'playlist': pl.name, 'item': pl.currentCue})

  def sendMpvOpts(self):
    self.sendEventResponse('set-mpv-opts', {'opts': self.state.mpvopts})

  def sendFileList(self, path, playlist, dirs, files):
    self.sendEventResponse('file-list', {'path': path, 'playlist': playlist, 'dirs': dirs, 'files': files})

  def clientCuePlaylist(self, name):
    self.sendEventResponse('cue-playlist', {'playlist': name})

  def clientStop(self):
    self.sendEventResponse('stopped')

  def clientPlay(self, playlist, item):
    self.sendEventResponse('playing', {'playlist': playlist, 'item': item})

  def clientMpvStarted(self):
    self.sendEventResponse('mpv-started')

  def clientMpvTerminated(self):
    self.sendEventResponse('mpv-terminated')

  def clientMpvUnexpectedTerminated(self):
    self.sendEventResponse('mpv-unexpected-termination')

  def clientKeepAlive(self):
    self.sendEventResponse('keep-alive')

  def tick(self):
    if(self.mpv != None):
      if(self.mpv.checkMPVRunning() == True):
        if(self.mpv.socket == None):
          if(time.monotonic() - self.lastConnectionAttempt >= 1):
            self.lastConnectionAttempt = time.monotonic()
            try:
              self.mpv.connect()
            except ConnectionRefusedError:
              print("Connection refused, socket not ready?")
            except FileNotFoundError:
              print("File not found, waiting on mpv...")
        else:
          if(self.connected == False):
            self.sendEventResponse("mpv-started")
            self.connected = True
          obj = self.mpv.getNextObj()
          
          if(obj != None):
            print("MPV --> " + repr(obj))
            if('event' in obj):
              if(obj['event'] == 'idle'):
                if(self.playing == True):
                  try:
                    self.playCurrentAndAdvance()
                  except PlaylistStop:
                    self.playing = False
                    self.clientStop()
                    self.clientCuePlaylist(None)
              elif(obj['event'] == 'start-file'):
                self.playing = True
                self.clientPlay(self.current[0], self.current[1])
      else:
        self.mpv.terminate()
        self.mpv = None
        self.connected = False
        self.playing = False
        self.clientMpvUnexpectedTerminated()

    if(self.socket.connected == False):
      self.socket.accept()
    else:
      if(self.lastAct == None):
        self.lastAct = time.monotonic()
      obj = None
      try:
        obj = self.socket.getJSONAsObj()
        self.lastAct = time.monotonic()
      except json.decoder.JSONDecodeError as e:
        self.sendFailureResponse("Bad JSON: " + e.args[0])
      if(obj == None):
        if(time.monotonic() - self.lastAct > MPVVJServer.TIMEOUT):
          print("Client connection timed out!")
          self.reconnectSocket()
      else:
        self.lastAct = time.monotonic()
        print("client --> " + repr(obj))
        if('command' in obj):
          if(obj['command'] == 'get-all-state'):
            self.sendPlaylists()
            for pl in self.state.playlists:
              if(len(pl.entries) != 0):
                self.sendPlaylist(pl)
            self.sendMpvOpts()

            # Make the client aware of our state where needed
            if(self.mpv != None):
              self.clientMpvStarted()
            else:
              self.clientMpvTerminated()

            current = self.state.getCurrent()
            if(current != None):
              self.clientCuePlaylist(current[0])

            if(self.playing == True):
              self.clientPlay(self.current[0], self.current[1])
          elif(obj['command'] == 'disconnect'):
            self.reconnectSocket()
          elif(obj['command'] == 'new-playlists'):
            command = obj['command']
            del obj['command']
            ret = self.state.newPlaylists(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'delete-playlists'):
            command = obj['command']
            del obj['command']
            ret = self.state.deletePlaylists(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'add-entries'):
            command = obj['command']
            del obj['command']
            ret = self.state.addEntries(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'delete-entries'):
            command = obj['command']
            del obj['command']
            ret = self.state.deleteEntries(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'cue-playlist'):
            command = obj['command']
            del obj['command']
            ret = self.state.setCurrentPlaylist(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'cue-item'):
            command = obj['command']
            del obj['command']
            ret = self.state.setPlaylistCurrentEntry(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'set-random'):
            command = obj['command']
            del obj['command']
            ret = self.state.setPlaylistRandom(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'set-looping'):
            command = obj['command']
            del obj['command']
            ret = self.state.setPlaylistLooping(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'set-played'):
            command = obj['command']
            del obj['command']
            ret = self.state.setPlayed(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)
          elif(obj['command'] == 'set-mpv-opts'):
            command = obj['command']
            del obj['command']
            ret = self.state.setMpvOpts(obj)
            if(ret != None):
              self.sendFailureResponse(command + ": " + ret)
            else:
              self.sendEventResponse(command, obj)            
          elif(obj['command'] == 'clear-all'):
            command = obj['command']
            del obj['command']
            self.state = MPVVJState.MPVVJState()
            self.sendEventResponse(command, obj)            
          elif(obj['command'] == 'play'):
            if(self.mpv != None):
              if(self.playing == True):
                self.mpv.stop()
              else:
                try:
                  self.playCurrentAndAdvance()
                  self.playing = True
                except PlaylistStop:
                  self.clientStop()
                  self.clientCuePlaylist(None)
            else:
              self.sendFailureResponse("MPV isn't running.")
              self.clientStop()
          elif(obj['command'] == 'stop'):
            if(self.playing == True):
              self.playing = False
              self.mpv.stop()
              self.clientStop()
            else:
              self.sendFailureResponse("Already stopped.")
          elif(obj['command'] == 'run-mpv'):
            if(self.mpv == None):
              self.mpv = MPV.MPV(MPVVJServer.DEFAULT_MPV, MPVVJServer.DEFAULT_SOCKET, self.state.mpvopts)
              self.lastConnectionAttempt = time.monotonic()
            else:
              self.sendFailureResponse("MPV is already running.")
          elif(obj['command'] == 'terminate-mpv'):
            if(self.mpv != None):
              self.mpv.terminate()
              self.mpv = None
              self.connected = False
              self.playing = False
              self.clientMpvTerminated()
            else:
              self.sendFailureResponse("MPV isn't running.")
          elif(obj['command'] == 'quit'):
            if(self.mpv != None):
              self.mpv.terminate()
            self.socket.close()
            return(False)
          elif(obj['command'] == 'list-files'):
            if('path' in obj):
              if(type(obj['path']) == str):
                if('playlist' in obj):
                  if(type(obj['playlist']) == str):
                    path = os.path.abspath(obj['path'])
                    if(path.startswith(self.path)):
                      path = path[len(self.path):]
                      path = "." + path
                      dirs = []
                      files = []
                      try:
                        for item in os.scandir(path):
                          if(item.is_file() == True):
                            files.append(item.name)
                          if(item.is_dir() == True):
                            dirs.append(item.name)
                        dirs.sort(key=lambda x: x.lower())
                        files.sort(key=lambda x: x.lower())
                        self.sendFileList(path, obj['playlist'], dirs, files)
                      except FileNotFoundError:
                        self.sendFailureResponse("File not found.")
                    else:
                      self.sendFailureResponse("'playlist' is not a string.")
                  else:
                    self.sendFailureResponse("No 'playlist'.")
                else:
                  self.sendFailureResponse("'path' outside of application root.")
              else:
                self.sendFailureResponse("'path' is not a string.")
            else:
              self.sendFailureResponse("No 'path'.")
          elif(obj['command'] == 'keep-alive'):
            self.clientKeepAlive()
          else:
            self.sendFailureResponse("Unknown action!")
        else:
          self.sendFailureResponse("JSON statement with nothing to do!")
    return(True)


if(__name__ == '__main__'):
  server = MPVVJServer()
  random.seed(time.time())

  try:
    while True:
      if(server.tick() == False):
        break
      time.sleep(1/TPS)
  except BaseException as e:
    if(server.socket != None):
      server.socket.close()
    raise e
