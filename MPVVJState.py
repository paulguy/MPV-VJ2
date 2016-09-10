"""
MPV-VJ2 Copyright 2016 paulguy <paulguy119@gmail.com>

This file is part of MPV-VJ2.

MPV-VJ2 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MPV-VJ2 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MPV-VJ2.  If not, see <http://www.gnu.org/licenses/>.
"""

import random


class PlaylistEntry:
  def __init__(self, item, played=False):
    if(type(item) != str):
      raise TypeError
    self.item = item
    self.played = played

  def setPlayed(self):
    self.played = True

  def setNotPlayed(self):
    self.played = False


class Playlist:
  def __init__(self, name, loop, random):
    if(type(name) != str):
      raise TypeError
    self.name = name
    self.entries = []
    self.currentCue = -1
    self.loop = loop
    self.random = random

  def insertEntry(self, value, played=False, idx=-1):
    if(idx < 0):
      self.entries.append(PlaylistEntry(value, played))
    else:
      self.entries.insert(idx, PlaylistEntry(value, played))
    if(self.currentCue == -1):
      self.currentCue = 0

  def delEntryByIndex(self, idx):
    del self.entries[idx]
    if(idx == self.currentCue):
      self.currentCue = -1
    elif(idx < self.currentCue):
      self.currentCue -= 1

  def getEntries(self):
    entries = []
    for entry in self.entries:
      entries.append({'name': entry.item, 'played': entry.played})

    return(entries)

  def setCurrent(self, idx):
    if(idx < 0 or idx > len(self.entries) - 1):
      raise IndexError

    self.currentCue = idx

  def getCurrent(self):
    return((self.currentCue, self.entries[self.currentCue].name))

  def advance(self):
    if(len(self.entries) == 0):
      raise RuntimeError("Empty playlist.")

    # this function is only used for advancing after something has been played
    # so set this now
    self.entries[self.currentCue].setPlayed()

    if(self.random == True):
      notPlayed = []
      for entry in enumerate(self.entries): # select an entry that hasn't been played
        if(entry[1].played == False):
          notPlayed.append(entry[0])

      if(len(notPlayed) == 0):
        if(self.loop == True):
          for entry in self.entries:
            entry.setNotPlayed()
            self.currentCue = random.randrange(len(self.entries))
        else:
          self.currentCue = -1
      else:
        self.currentCue = notPlayed[random.randrange(len(notPlayed))]
    else:
      if(self.currentCue == len(self.entries) - 1):
        if(self.loop == True):
          for entry in self.entries:
            entry.setNotPlayed()
          self.currentCue = 0
        else:
          self.currentCue = -1
      else:
        self.currentCue += 1


class MPVVJState:
  def __init__(self):
    self.playlists = []
    self.mpvopts = {}
    self.currentPlaylist = None

  def findPlaylistByName(self, name):
    for pl in enumerate(self.playlists):
      if(pl[1].name == name):
        return(pl)

    return(None)

  def newPlaylist(self, name, loop, random):
    self.playlists.append(Playlist(name, loop, random))

  def newPlaylists(self, obj):
    if('playlists' not in obj):
      return("No 'playlists'.")
    if(type(obj['playlists']) != list):
      return("'playlists' is not a list.")
    for item in enumerate(obj['playlists']):
      if(type(item[1]) != dict):
        return("'playlists' item not a dict.")
      if('name' not in item[1]):
        return("'playlists' item with no 'name'.")
      if(type(item[1]['name']) != str):
        return("'name' is not a string.")
      try:
        if(type(item[1]['loop']) != bool):
          return("'loop' is not a bool.")
      except KeyError:
        pass
      try:
        if(type(item[1]['random']) != bool):
          return("'random' is not a bool.")
      except KeyError:
        pass

      if(self.findPlaylistByName(item[1]['name']) != None):
        return("Playlist item '" + item[1]['name'] + "' already exists.")
      for item2 in enumerate(obj['playlists']):
        if(item[0] == item2[0]):
          continue
        if(item[1]['name'] == item2[1]['name']):
          return("Duplicate name '" + item[1]['name'] + "'.")

    for item in obj['playlists']:
      loop = False
      random = False
      try:
        loop = item['loop']
      except KeyError:
        pass
      try:
        random = item['random']
      except KeyError:
        pass
      
      self.newPlaylist(item['name'], loop, random)
    return(None)

  def deletePlaylist(self, idx):
    if(self.currentPlaylist == idx):
      self.currentPlaylist = None
    del self.playlists[idx]

  def deletePlaylists(self, obj):
    if('playlists' not in obj):
      return("No 'playlists' list.")
    if(type(obj['playlists']) != list):
      return("'playlists' is not a list.")
    indices = []
    for item in obj['playlists']:
      if(type(item) != str):
        return("'playlists' item not a string.")
      pl = self.findPlaylistByName(item)
      if(pl == None):
        return("Playlist " + item + " does not exist.")
      indices.append(pl[0])
    
    for idx in indices:
      self.deletePlaylist(idx)
    return(None)

  def addEntries(self, obj):
    if('playlist' not in obj):
      return("No 'playlist'.")
    if(type(obj['playlist']) != str):
      return("'playlist' is not a string.")
    pl = self.findPlaylistByName(obj['playlist'])
    if(pl == None):
      return("Playlist " + obj['playlist'] + " does not exist.")
    if('entries' not in obj):
      return("No 'entries'.")
    if(type(obj['entries']) != list):
      return("'entries' is not a list.")
    location = -1
    try:
      if(type(obj['location']) != int):
        return("'location' is not an integer.")
      else:
        location = obj['location']
    except KeyError:
      pass
    for item in obj['entries']:
      if(type(item) != dict):
        return("'entries' item is not a dict.")
      if('name' not in item):
        return("'entries' item with no 'name'.")
      if(type(item['name']) != str):
        return("'name' is not a string.")
      try:
        if(type(item['played']) != bool):
          return("'played' is not a bool.")
      except KeyError:
        pass
        
    for item in obj['entries']:
      played = False
      try:
        played = item['played']
      except KeyError:
        pass
      
      pl[1].insertEntry(item['name'], played, location)
      if(location >= 0):
        location += 1
    return(None)

  def deleteEntries(self, obj):
    if('playlist' not in obj):
      return("No 'playlist'.")
    if(type(obj['playlist']) != str):
      return("'playlist' is not a string.")
    pl = self.findPlaylistByName(obj['playlist'])
    if(pl == None):
      return("Playlist " + obj['playlist'] + " does not exist.")
    if('entries' not in obj):
      return("No 'entries' list.")
    if(type(obj['entries']) != list):
      return("'entries' is not a list.")
    lastEntry = len(pl[1].entries) - 1
    for entry in obj['entries']:
      if(type(entry) != int):
        return("'entries' item is not an int.")
      if(entry < 0 or entry > lastEntry):
        return("Entry " + str(entry) + " out of range.")

    for entry in obj['entries']:
      pl[1].delEntryByIndex(entry)
    return(None)

  def getPlaylists(self):
    playlists = []
    for pl in self.playlists:
      playlists.append({'name': pl.name, 'random': pl.random, 'loop': pl.loop, 'current': pl.currentCue})
      
    return(playlists)

  def setCurrentPlaylist(self, obj):
    if('playlist' not in obj):
      return("No 'playlist'.")
    if(obj['playlist'] == None):
      self.currentPlaylist = None
      return(None)
    if(type(obj['playlist']) != str):
      return("'playlist' is not a string.")
    pl = self.findPlaylistByName(obj['playlist'])
    if(pl == None):
      return("Playlist " + obj['playlist'] + " does not exist.")
    if(len(pl[1].entries) == 0):
      return("Playlist " + obj['playlist'] + " has no entries.")

    self.currentPlaylist = pl[0]
    return(None)

  def setPlaylistCurrentEntry(self, obj):
    if('playlist' not in obj):
      return("No 'playlist'.")
    if(type(obj['playlist']) != str):
      return("'playlist' is not a string.")
    pl = self.findPlaylistByName(obj['playlist'])
    if(pl == None):
      return("Playlist " + obj['playlist'] + " does not exist.")
    if('item' not in obj):
      return("No 'item'.")
    if(type(obj['item']) != int):
      return("'item' is not an integer.")
    if(obj['item'] < 0 or obj['item'] > len(pl[1].entries) - 1):
      return("'item'=" + str(obj['item']) + " out of range.")
    
    pl[1].setCurrent(obj['item'])
    return(None)

  def setPlaylistRandom(self, obj):
    if('playlist' not in obj):
      return("No 'playlist'.")
    if(type(obj['playlist']) != str):
      return("'playlist' is not a string.")
    pl = self.findPlaylistByName(obj['playlist'])
    if(pl == None):
      return("Playlist " + obj['playlist'] + " does not exist.")
    value = None
    try:
      if(type(obj['value']) != bool):
        return("'value' is not a bool.")
      value = obj['value']
    except KeyError:
      pass
    if(value == None):
      pl[1].random = not pl[1].random
    else:
      pl[1].random = value
    return(None)

  def setPlaylistLooping(self, obj):
    if('playlist' not in obj):
      return("No 'playlist'.")
    if(type(obj['playlist']) != str):
      return("'playlist' is not a string.")
    pl = self.findPlaylistByName(obj['playlist'])
    if(pl == None):
      return("Playlist " + obj['playlist'] + " does not exist.")
    value = None
    try:
      if(type(obj['value']) != bool):
        return("'value' is not a bool.")
      value = obj['value']
    except KeyError:
      pass
    if(value == None):
      pl[1].loop = not pl[1].loop
    else:
      pl[1].loop = value
    return(None)

  def setMpvOpts(self, obj):
    if('opts' not in obj):
      return("No 'opts'.")
    if(type(obj['opts']) != dict):
      return("'opts' is not a dict.")
    for key in obj['opts'].keys():
      if(type(key) != str):
        return("Option key isn't a string.")
      if(type(obj['opts'][key]) != str):
        return("Option value isn't a string.")
    self.mpvopts = obj['opts']
    return(None)

  def addMPVOpt(self, name, value):
    if(type(name) != str or type(value) != str):
      raise TypeError

    self.mpvopts.append((name, value))

  def findMPVOptsByName(self, name):
    opts = []

    for opt in enumerate(self.mpvopt):
      if(opt[1].name == name):
        opts.append(opt)

    return(opts)

  def delMPVOptsByName(self, name):
    opts = self.findMPVOptsByName(name)
    
    for opt in opts:
      del self.mpvopts[opt[0]]
      
    return(len(opts))

  def getCurrent(self):
    if(self.currentPlaylist == None): # no playlist selected
      return(None)
    currentPlaylist = self.playlists[self.currentPlaylist]
    if(len(currentPlaylist.entries) == 0): # empty playlist selected
      return(None)
    if(currentPlaylist.currentCue == -1): # reached end
      return(None)
    return(currentPlaylist.name,
           currentPlaylist.currentCue,
           currentPlaylist.entries[currentPlaylist.currentCue].item)

  def advance(self):
    if(self.currentPlaylist == None): # no playlist selected
      raise RuntimeError("No playlist selected.")
    currentPlaylist = self.playlists[self.currentPlaylist]
    if(len(currentPlaylist.entries) == 0): # empty playlist selected
      raise RuntimeError("Empty playlist.")
    currentPlaylist.advance()
