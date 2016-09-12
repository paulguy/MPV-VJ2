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


import socket
import json
import selectors
import os

class JSONSocket:
  RECVREAD = 32768

  def accept(self):
    if(self.listenSocket == None):
      raise RuntimeError("Not a listening socket.")
    try:
      sock, addr = self.listenSocket.accept()
    except BlockingIOError:
      return(False)

    self.listenSocket.shutdown(socket.SHUT_RDWR)
    self.listenSocket.close()
    self.listenSocket = None
    self.socket = sock
    self.socket.setblocking(False)
    self.IP = addr
    self.connected = True
    self.recvlinebuff = b''
    return(True)

  def close(self):
    if(self.listenSocket != None):
      try:
        self.listenSocket.shutdown(socket.SHUT_RDWR)
      except OSError:
        pass
      self.listenSocket.close()
      self.listenSocket = None
    if(self.socket != None):
      try:
        self.socket.shutdown(socket.SHUT_RDWR)
      except OSError:
        pass
      self.socket.close()
      self.socket = None
    if(self.selector != None):
      self.selector.close()
      self.selector = None
    self.connected = False

  def readSocketLine(self):
    if(self.connected == False):
      if(self.selector == None):
        raise ConnectionError("Not connected.")

      if(self.selector.select(timeout=0) == []):
        return(None)
      else:
        self.selector.close()
        self.selector = None
        self.connected = True
    
    while True: # empty the buffer entirely
      try:
        readbuf = self.socket.recv(JSONSocket.RECVREAD)
        # when a Unix socket closes, we end up just reading empty buffers
        if(len(readbuf) == 0):
          break
        self.recvlinebuff += readbuf
      except BlockingIOError:
        break

    lineidx = 0
    try:
      lineidx = self.recvlinebuff.index(b'\n')
    except ValueError:
      return(None)

    line = self.recvlinebuff[:lineidx]
    self.recvlinebuff = self.recvlinebuff[lineidx+1:]

    return(line.decode('utf-8', errors='replace'))

  def sendObjAsJSON(self, obj):
    if(self.connected == False):
      if(self.selector == None):
        raise ConnectionError("Not connected.")
    try:
      self.socket.send((json.dumps(obj) + "\n").encode('utf-8'))
    except BrokenPipeError as e:
      self.connected = False
      raise e

  def getJSONAsObj(self):
    line = self.readSocketLine()
    if(line == None):
      return(None)

    return(json.loads(line))

class JSONTCPSocket(JSONSocket):
  # Because of getaddrinfo() this method could block for a while, but there's no
  # better way.  Could present a "hung" interface to the user during.
  def __init__(self, listening, port, host):
    self.connected = False
    self.selector = None
    self.listenSocket = None
    self.socket = None
    self.listening = listening

    if(host != None and type(host) != str):
      raise TypeError
    if(type(port) != int):
      raise TypeError
    if(port < 1 or port > 65535):
      raise ValueError("port must be between 1 and 65535.")
    self.host = host
    self.port = port

    if(listening == False):
      if(self.host == None or self.port == None):
        raise ValueError("host and port must be set for connecting socket.")

      ais = socket.getaddrinfo(self.host, self.port, family=socket.AF_UNSPEC,
                              type=socket.SOCK_STREAM)
      sockaddr = None
      for addrinfo in ais:
        try:
          self.socket = socket.socket(family=addrinfo[0], type=addrinfo[1], proto=addrinfo[2])
        except OSError:
          continue
        try:
          self.socket.setblocking(False)
          self.socket.connect(addrinfo[4])
        except BlockingIOError:
          sockaddr = addrinfo[4]
          break
        except OSError:
          self.socket.close()
          continue

      if(sockaddr == None):
        raise ConnectionError("No valid addresses found for " + self.host + " (" + str(self.port) + ").")
      self.IP = sockaddr[1]
      self.selector = selectors.DefaultSelector()
      self.selector.register(self.socket, selectors.EVENT_WRITE)
      self.recvlinebuff = b''
      self.preconnectbuff = b''
    else:
      ais = socket.getaddrinfo(self.host, self.port, family=socket.AF_UNSPEC,
                              type=socket.SOCK_STREAM, flags=socket.AI_PASSIVE)
      sockaddr = None
      for addrinfo in ais:
        try:
          self.listenSocket = socket.socket(family=addrinfo[0], type=addrinfo[1], proto=addrinfo[2])
        except OSError:
          continue
        try:
          self.listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          self.listenSocket.bind(addrinfo[4])
          self.listenSocket.listen(0)
          self.listenSocket.setblocking(False)
        except OSError:
          self.listenSocket.close()
          continue
        sockaddr = addrinfo[4]
        break

      if(sockaddr == None):
        if(self.host == None):
          raise ConnectionError("Couldn't bind to 0.0.0.0:" + str(self.port) + ".")
        else:
          raise ConnectionError("Couldn't bind to " + self.host + " (" + str(self.port) + ").")


class JSONUnixSocket(JSONSocket):
  def __init__(self, listening, path):
    self.connected = False
    self.selector = None
    self.listenSocket = None
    self.socket = None
    self.listening = listening

    if(type(path) != str):
      raise TypeError
    self.path = path
    
    if(listening == False):
      self.socket = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM)
      self.socket.setblocking(False)
      self.socket.connect(self.path)
      self.selector = selectors.DefaultSelector()
      self.selector.register(self.socket, selectors.EVENT_WRITE)
      self.recvlinebuff = b''
      self.preconnectbuff = b''
    else:
      os.remove(self.path)
      
      self.listenSocket = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM,
                                  flags=socket.AI_PASSIVE)
      self.listenSocket.setblocking(False)
      self.listenSocket.bind(self.path)
      self.listenSocket.listen(0)

  def close(self):
    super().close()
    os.remove(self.path)
