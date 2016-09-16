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


import subprocess
import JSONSocket


class MPV:
    RETRIES = 3

    MPV_FORCED_OPTS = {
        'config': 'no',
        'idle': 'yes',
        'terminal': 'no',
    }

    def __init__(self, path, socket, opts):
        if type(path) != str or type(opts) != dict:
            raise TypeError
        for item in opts.keys():
            if type(item) != str:
                raise TypeError
            if type(opts[item]) != str:
                raise TypeError
        self.path = path
        self.socketName = socket
        self.opts = opts
        self.forcedOpts = MPV.MPV_FORCED_OPTS
        self.forcedOpts['input-ipc-server'] = self.socketName

        self.mpv = None
        self.run()
        self.socket = None

    def checkMPVRunning(self):
        if self.mpv is None:
            return False

        self.mpv.poll()

        if self.mpv.returncode is not None:
            self.mpv = None
            return False

        return True

    @staticmethod
    def genArgs(args):
        arglist = []

        for item in args.keys():
            if len(args[item]) == 0:
                arglist.append('--' + item + '=yes')
            else:
                arglist.append('--' + item + '=' + args[item])

        return arglist

    def run(self):
        if self.checkMPVRunning():
            raise RuntimeError("MPV is already running!")

        opts = self.opts.copy()
        opts.update(self.forcedOpts)
        arglist = MPV.genArgs(opts)
        textArgs = ""
        for arg in arglist:
            textArgs = textArgs + " " + arg
        print("Running " + self.path + textArgs)
        self.mpv = subprocess.Popen(arglist, stdout=subprocess.DEVNULL,
                                    stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def terminate(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        if self.mpv is not None:
            self.mpv.terminate()
            self.mpv = None

    def connect(self):
        self.socket = JSONSocket.JSONUnixSocket(path=self.socketName, listening=False)

    def sendCommand(self, command, args=None, request_id=None):
        if self.socket is None:
            raise RuntimeError("No connection to MPV.")

        if args is None:
            args = [command]
        else:
            if type(args) != list:
                args = list(args)
            args.insert(0, command)

        obj = {'command': args}
        if request_id is not None:
            obj['request_id'] = request_id

        print("MPV <-- " + repr(obj))
        self.socket.sendObjAsJSON(obj)

    def play(self, uri):
        self.sendCommand('loadfile', [uri])

    def stop(self):
        self.sendCommand('stop')

    def getNextObj(self):
        return self.socket.getJSONAsObj()
