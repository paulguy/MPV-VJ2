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
import argparse

import MPVVJState
import JSONSocket
import MPV

# TODO
# MPV options management - DONE
# new/save/load (and client) - DONE
# file browsing (and client) - DONE
# command line arguments (bind address, port, verbose logging, starting directory, ...) - DONE
# probably some more socket stuff as it comes up... - SEEMINGLY DONE!
# unset all played in playlist (and clioent)
# playlist organization (and client)
# bugs and crashes

TPS = 20
DEFAULT_MPV = "/usr/bin/mpv"
DEFAULT_SOCKET = "/tmp/mpvsocket"
DEFAULT_PORT = 12345
DEFAULT_BIND_ADDRESS = "127.0.0.1"


def hupHandler(signum, frame):
    print("SIGHUP received.")
    try:
        server
    except NameError:
        return

    if server.socket is not None:
        server.reconnectSocket()
        print("Listening socket forcibly closed and reopened")


class PlaylistStop(BaseException):
    pass


class MPVVJServer():
    RETRIES = 3
    TIMEOUT = 45

    def __init__(self, mpvPath, socketPath, bindAddress, port):
        self.mpvPath = mpvPath
        self.socketPath = socketPath
        self.bindAddress = bindAddress
        self.port = port
        self.state = MPVVJState.MPVVJState()
        self.socket = None
        self.reconnectSocket()
        self.mpv = None
        self.connected = False
        self.playing = False
        self.path = os.getcwd()
        signal.signal(signal.SIGHUP, hupHandler)

        self.current = None
        self.lastAct = None
        self.lastConnectionAttempt = 0

    def reconnectSocket(self):
        if self.socket is not None:
            self.socket.close()
        print("Binding to " + self.bindAddress + " (" + str(self.port) + ").")
        self.socket = JSONSocket.JSONTCPSocket(listening=True, host=self.bindAddress,
                                               port=self.port)
        self.lastAct = None

    def sendResponse(self, responseType, value, args=None):
        if args is None:
            args = {responseType: value}
        else:
            if type(args) != dict:
                raise TypeError
            args.update({responseType: value})

        if self.socket is not None and self.socket.connected:
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
        if data is None:
            self.sendStatusResponse('success')
        else:
            self.sendStatusResponse('success', {'data': data})

    def sendFailureResponse(self, message=None):
        if message is None:
            self.sendStatusResponse('failure')
        else:
            if type(message) != str:
                raise TypeError
            self.sendStatusResponse('failure', {'message': message})

    def playCurrentAndAdvance(self):
        # since hopefully there's no other way for mpv to emit a 'start-file' event
        # we set this now so once mpv gets the event, we can tell the client which
        # item is playing.
        self.current = self.state.getCurrent()
        if self.current is None:
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
        self.mpv.terminate()
        self.mpv = None
        self.connected = False
        self.playing = False
        self.sendEventResponse('mpv-unexpected-termination')

    def clientKeepAlive(self):
        self.sendEventResponse('keep-alive')

    def tick(self):
        if self.mpv is not None:
            if self.mpv.checkMPVRunning():
                if self.mpv.socket is None:
                    if time.monotonic() - self.lastConnectionAttempt >= 1:
                        self.lastConnectionAttempt = time.monotonic()
                        try:
                            self.mpv.connect()
                        except ConnectionRefusedError:
                            print("Connection refused, socket not ready?")
                        except FileNotFoundError:
                            print("File not found, waiting on mpv...")
                else:
                    if not self.connected:
                        self.sendEventResponse("mpv-started")
                        self.connected = True
                    try:
                        obj = self.mpv.getNextObj()

                        if obj is not None:
                            print("MPV --> " + repr(obj))
                            if 'event' in obj:
                                if obj['event'] == 'idle':
                                    if self.playing:
                                        try:
                                            self.playCurrentAndAdvance()
                                        except PlaylistStop:
                                            self.playing = False
                                            self.clientStop()
                                            self.clientCuePlaylist(None)
                                elif obj['event'] == 'start-file':
                                    self.playing = True
                                    self.clientPlay(self.current[0], self.current[1])
                    except ConnectionError as e:
                        print("MPV connection error: " + e.args[0])
                        self.clientMpvUnexpectedTerminated()
            else:
                self.clientMpvUnexpectedTerminated()

        if not self.socket.connected:
            self.socket.accept()
        else:
            if self.lastAct is None:
                self.lastAct = time.monotonic()
            obj = None
            try:
                obj = self.socket.getJSONAsObj()
                self.lastAct = time.monotonic()
            except json.decoder.JSONDecodeError as e:
                self.sendFailureResponse("Bad JSON: " + e.args[0])
            except ConnectionError as e:
                print("Client connection error: " + e.args[0])
                self.reconnectSocket()
                return True
            if obj is None:
                if time.monotonic() - self.lastAct > MPVVJServer.TIMEOUT:
                    print("Client connection timed out!")
                    self.reconnectSocket()
            else:
                self.lastAct = time.monotonic()
                print("client --> " + repr(obj))
                if 'command' in obj:
                    if obj['command'] == 'get-all-state':
                        self.sendPlaylists()
                        for pl in self.state.playlists:
                            if (len(pl.entries) != 0):
                                self.sendPlaylist(pl)
                        self.sendMpvOpts()

                        # Make the client aware of our state where needed
                        if self.mpv is not None:
                            self.clientMpvStarted()
                        else:
                            self.clientMpvTerminated()

                        current = self.state.getCurrent()
                        if current is not None:
                            self.clientCuePlaylist(current[0])

                        if self.playing:
                            self.clientPlay(self.current[0], self.current[1])
                    elif obj['command'] == 'disconnect':
                        self.reconnectSocket()
                    elif obj['command'] == 'new-playlists':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.newPlaylists(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'delete-playlists':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.deletePlaylists(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'add-entries':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.addEntries(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'delete-entries':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.deleteEntries(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'cue-playlist':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.setCurrentPlaylist(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'cue-item':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.setPlaylistCurrentEntry(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'set-random':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.setPlaylistRandom(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'set-looping':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.setPlaylistLooping(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'set-played':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.setPlayed(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'set-mpv-opts':
                        command = obj['command']
                        del obj['command']
                        ret = self.state.setMpvOpts(obj)
                        if ret is not None:
                            self.sendFailureResponse(command + ": " + ret)
                        else:
                            self.sendEventResponse(command, obj)
                    elif obj['command'] == 'clear-all':
                        command = obj['command']
                        del obj['command']
                        self.state = MPVVJState.MPVVJState()
                        self.sendEventResponse(command, obj)
                    elif obj['command'] == 'play':
                        if self.mpv is not None:
                            if self.playing:
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
                    elif obj['command'] == 'stop':
                        if self.playing:
                            self.playing = False
                            self.mpv.stop()
                            self.clientStop()
                        else:
                            self.sendFailureResponse("Already stopped.")
                    elif obj['command'] == 'run-mpv':
                        if self.mpv is None:
                            self.mpv = MPV.MPV(self.mpvPath, self.socketPath, self.state.mpvopts)
                            self.lastConnectionAttempt = time.monotonic()
                        else:
                            self.sendFailureResponse("MPV is already running.")
                    elif obj['command'] == 'terminate-mpv':
                        if self.mpv is not None:
                            self.mpv.terminate()
                            self.mpv = None
                            self.connected = False
                            self.playing = False
                            self.clientMpvTerminated()
                        else:
                            self.sendFailureResponse("MPV isn't running.")
                    elif obj['command'] == 'list-files':
                        if 'path' in obj:
                            if type(obj['path']) == str:
                                if 'playlist' in obj:
                                    if type(obj['playlist']) == str:
                                        path = os.path.abspath(obj['path'])
                                        if path.startswith(self.path):
                                            path = path[len(self.path):]
                                            path = "." + path
                                            dirs = []
                                            files = []
                                            try:
                                                for item in os.scandir(path):
                                                    if item.is_file():
                                                        files.append(item.name)
                                                    if item.is_dir():
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
                    elif obj['command'] == 'keep-alive':
                        self.clientKeepAlive()
                    else:
                        self.sendFailureResponse("Unknown action!")
                else:
                    self.sendFailureResponse("JSON statement with nothing to do!")
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MPV-VJ2 - Remotely control mpv and manage playlists.")
    parser.add_argument('--mpv-path', metavar="<PATH>", type=str,
                        help="Path to MPV executable.", default=DEFAULT_MPV)
    parser.add_argument('--mpv-socket-path', metavar="<PATH>", type=str,
                        help="Filename of socket to use for communicating with mpv.",
                        default=DEFAULT_SOCKET)
    parser.add_argument('--bind-address', metavar="<address>", type=str,
                        help="Address to bind to.", default=DEFAULT_BIND_ADDRESS)
    parser.add_argument('--bind-port', metavar="<port>", type=int,
                        help="Port to bind to.", default=DEFAULT_PORT)
    args = parser.parse_args()

    server = MPVVJServer(args.mpv_path, args.mpv_socket_path,
                         args.bind_address, args.bind_port)
    random.seed(time.time())

    try:
        while True:
            if not server.tick():
                break
            time.sleep(1 / TPS)
    except BaseException as e:
        if server.socket is not None:
            server.socket.close()
        raise e
