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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Gdk
from gi.repository import Gio

import PromptDialog
import SettingsDialog


class MainWindow(Gtk.Window):
  def getListBoxLabel(text):
    label = Gtk.Label(text)
    label.set_halign(Gtk.Align.START)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    label.show()
    return(label)

  def newPlaylistResponse(self, dialog, response):
    if(response == Gtk.ResponseType.OK):
      self.client.newPlaylist(dialog.get_text())
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()

  def newPlaylist(self, button):
    dialog = PromptDialog.PromptDialog(self, "New Playlist")
    dialog.connect('response', self.newPlaylistResponse)
    dialog.show_all()

  def editSettingsResponse(self, dialog, response):
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()

  def editSettings(self, button):
    settingsDialog = SettingsDialog.SettingsDialog(self, self.client.settings)
    settingsDialog.connect('response', self.editSettingsResponse)
    settingsDialog.show_all()

  def editMpvOptsResponse(self, dialog, response):
    self.client.sendOpts()
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()

  def editMpvOpts(self, button):
    settingsDialog = SettingsDialog.SettingsDialog(self, self.client.getOpts(), add=True)
    settingsDialog.connect('response', self.editMpvOptsResponse)
    settingsDialog.show_all()

  def connectClient(self, button):
    self.client.connect()

  def setSensitive(self, sensitive):
    if(sensitive == False):
      self.playlistsListStore.clear()
      self.playlist1ListStore.clear()
      self.playlist2ListStore.clear()
      self.playlist1Label.set_text("")
      self.playlist2Label.set_text("")
      self.mpvBtn.set_sensitive(False)
      self.playBtn.set_sensitive(False)
      self.stopBtn.set_sensitive(False)
      self.mpvOptsBtn.set_sensitive(False)
      if(self.mpvHandlerID != None):
        self.mpvBtn.disconnect(self.mpvHandlerID)
        self.mpvHandlerID = None
    self.connectBtn.set_sensitive(sensitive)
    self.addBtn.set_sensitive(sensitive)
    self.addUrl1Btn.set_sensitive(sensitive)
    self.addFiles1Btn.set_sensitive(sensitive)
    self.addUrl2Btn.set_sensitive(sensitive)
    self.addFiles2Btn.set_sensitive(sensitive)
    self.newBtn.set_sensitive(sensitive)
    self.loadBtn.set_sensitive(sensitive)
    self.saveBtn.set_sensitive(sensitive)
    self.playlistsList.set_sensitive(sensitive)
    self.playlist1List.set_sensitive(sensitive)
    self.playlist2List.set_sensitive(sensitive)

  def disconnectClient(self, button):
    self.setSensitive(False)
    self.client.disconnect()

  def refreshPlaylistView(self, playlistView, name):
    playlistStore = playlistView.get_children()[2].get_children()[0].get_model()
    
    playlistStore.clear()
    
    if(name != None):
      playlistView.get_children()[1].set_text(name)

      current, entries = self.client.getPlaylistEntries(name)
      for entry in enumerate(entries):
        state = ''
        played = 'N'
        if(entry[0] == current):
          state = 'C'
        if(self.playlistPlaying == name):
          if(entry[0] == self.mediaPlaying):
            state = 'P'
        try:
          if(entry[1]['played'] == True):
            played = 'Y'
        except KeyError:
          pass
        playlistStore.append((state, entry[1]['name'], played))
    else:
      playlistView.get_children()[1].set_text("")

  def playlistItemActions(self, playlistList, event):
    model, rows = playlistList.get_selection().get_selected_rows()

    if(len(rows) == 0):
      return(False)

    if(event.type == Gdk.EventType.KEY_PRESS):
      if(event.keyval == Gdk.KEY_l):
        if(len(rows) == 1):
          pl = model.get_value(model.get_iter(rows[0]), 1)
          if(self.playlist2Label.get_text() == pl):
            return(False)
          self.refreshPlaylistView(self.playlist1View, pl)
      elif(event.keyval == Gdk.KEY_r):
        if(len(rows) == 1):
          pl = model.get_value(model.get_iter(rows[0]), 1)
          if(self.playlist1Label.get_text() == pl):
            return(False)
          self.refreshPlaylistView(self.playlist2View, pl)
      elif(event.keyval == Gdk.KEY_c):
        if(len(rows) == 1):
          pl = model.get_value(model.get_iter(rows[0]), 1)
          self.client.cuePlaylist(pl)
      elif(event.keyval == Gdk.KEY_d):
        pls = []
        for row in rows:
          pls.append(model.get_value(model.get_iter(row), 1))
        self.client.deletePlaylists(pls)
    return(False)

  def playlistActions(self, playlistView, event, label):
    playlist = playlistView.get_children()[2].get_children()[0]
    model, rows = playlist.get_selection().get_selected_rows()

    if(len(rows) == 0):
      return(False)

    if(event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS):
      if(event.button == 1):
        if(len(rows) == 1):
          pl = label.get_text()
          self.client.cuePlaylist(pl)
          self.client.cueEntry(pl, rows[0].get_indices()[0])
          self.client.playMedia()

    if(event.type == Gdk.EventType.KEY_PRESS):
      if(event.keyval == Gdk.KEY_c):
        if(len(rows) == 1):
          pl = label.get_text()
          self.client.cueEntry(pl, rows[0].get_indices()[0])
      if(event.keyval == Gdk.KEY_d):
        pl = label.get_text()
        items = []
        for row in rows:
          items.append(row.get_indices()[0])
        self.client.deleteEntries(pl, items)
    return(False)

  def addURLResponse(self, dialog, response, playlistLabel):
    if(response == Gtk.ResponseType.OK):
      self.client.addEntry(playlistLabel.get_text(), dialog.get_text())
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()    

  def addURL(self, button, playlistLabel):
    if(playlistLabel.get_text() == ''):
      return
    dialog = PromptDialog.PromptDialog(self, "Add URL")
    dialog.connect('response', self.addURLResponse, playlistLabel)
    dialog.show_all()

  def startMPV(self, button):
    self.mpvBtn.set_sensitive(False)
    self.client.startMPV()

  def stopMPV(self, button):
    self.mpvBtn.set_sensitive(False)
    self.client.stopMPV()

  def playMedia(self, button):
    self.playBtn.set_sensitive(False)
    self.client.playMedia()

  def stopMedia(self, button):
    self.stopBtn.set_sensitive(False)
    self.client.stopMedia()

  # event inputs

  def newPlaylists(self, obj):
    for item in obj['playlists']:
      random = 'N'
      loop = 'N'
      try:
        if(item['random'] == True):
          random = 'Y'
      except KeyError:
        pass
      try:
        if(item['loop'] == True):
          loop = 'Y'
      except KeyError:
        pass
      self.playlistsListStore.append(('', item['name'], random, loop))

  def deletePlaylists(self, obj):
    for pl in obj['playlists']:
      for row in self.playlistsListStore:
        if(row[1] == pl):
          if(self.playlist1Label.get_text() == pl):
            self.refreshPlaylistView(self.playlist1View, None)
          elif(self.playlist2Label.get_text() == pl):
            self.refreshPlaylistView(self.playlist2View, None)
          self.playlistsListStore.remove(row.iter)

  def setCurrentPlaylist(self, obj):
    for row in self.playlistsListStore:
      if(obj['playlist'] == row[1]):
        row[0] = 'C'
      elif(row[0] == 'C'):
        row[0] = ''

  def cueItem(self, obj):
    playlist = None
    if(self.playlist1Label.get_text() == obj['playlist']):
      playlist = self.playlist1ListStore
    elif(self.playlist2Label.get_text() == obj['playlist']):
      playlist = self.playlist2ListStore

    if(playlist != None):
      for row in enumerate(playlist):
        if(row[1][0] == 'C' and playlist[0] != obj['item']):
          row[1][0] = ''
          break

      playlist[obj['item']][0] = 'C'

  def addEntries(self, obj):
    playlist = None
    if(self.playlist1Label.get_text() == obj['playlist']):
      playlist = self.playlist1ListStore
    elif(self.playlist2Label.get_text() == obj['playlist']):
      playlist = self.playlist2ListStore
    
    if(playlist != None):
      i = None
      try:
        i = playlist.get_iter(Gtk.TreePath.new_from_indices([obj['location']]))
      except KeyError:
        pass
      for entry in obj['entries']:
        played = 'N'
        try:
          if(entry['played'] == True):
            played = 'Y'
        except KeyError:
          pass
        if(i == None):
          playlist.append(('', entry['name'], played))
        else:
          playlist.insert_before(i, ('', entry['name'], played))
          i = playlist.iter_next(i)

  def clientConnected(self):
    self.connectBtn.get_children()[0].set_from_icon_name('network-offline', Gtk.IconSize.BUTTON)
    self.connectBtn.disconnect(self.connectHandlerID)
    self.connectHandlerID = self.connectBtn.connect('clicked', self.disconnectClient)
    self.setSensitive(True)

  def clientDisconnected(self):
    if(self.is_visible() == True): # avoid exception on close when still connected
      self.connectBtn.get_children()[0].set_from_icon_name('network-idle', Gtk.IconSize.BUTTON)
      self.connectBtn.disconnect(self.connectHandlerID)
      self.connectHandlerID = self.connectBtn.connect('clicked', self.connectClient)
      self.connectBtn.set_sensitive(True)

  def MPVStarted(self):
    self.mpvBtn.get_children()[0].set_from_icon_name('go-down', Gtk.IconSize.BUTTON)
    if(self.mpvHandlerID != None):
      self.mpvBtn.disconnect(self.mpvHandlerID)
    self.mpvHandlerID = self.mpvBtn.connect('clicked', self.stopMPV)
    self.mpvBtn.set_sensitive(True)
    
    # make transport buttons sensitive
    if(self.mediaPlaying != None):
      self.playBtn.get_children()[0].set_from_icon_name('media-skip-forward', Gtk.IconSize.BUTTON)
      self.stopBtn.set_sensitive(True)
    self.playBtn.set_sensitive(True)
    
    self.mpvRunning = True

  def MPVStopped(self):
    self.mpvBtn.get_children()[0].set_from_icon_name('go-up', Gtk.IconSize.BUTTON)
    if(self.mpvHandlerID != None):
      self.mpvBtn.disconnect(self.mpvHandlerID)
    self.mpvHandlerID = self.mpvBtn.connect('clicked', self.startMPV)
    self.mpvBtn.set_sensitive(True)

    # make transport buttons insensitive
    self.playBtn.set_sensitive(False)
    self.stopBtn.set_sensitive(False)

    self.mpvRunning = False

    self.stopped()

  def playing(self, obj):
    playlist = None
    if(self.playlist1Label.get_text() == obj['playlist']):
      playlist = self.playlist1ListStore
    elif(self.playlist2Label.get_text() == obj['playlist']):
      playlist = self.playlist2ListStore
    
    if(playlist != None):
      for row in playlist:
        if(row[0] == 'P'):
          row[0] = ''
          
      playlist[obj['item']][0] = 'P'

    self.playBtn.get_children()[0].set_from_icon_name('media-skip-forward', Gtk.IconSize.BUTTON)
    self.playBtn.set_sensitive(True)
    self.stopBtn.set_sensitive(True)

    self.mediaPlaying = obj['item']
    self.playlistPlaying = obj['playlist']

  def stopped(self):
    for row in self.playlist1ListStore:
      if(row[0] == 'P'):
        row[0] = ''
        break
    for row in self.playlist2ListStore:
      if(row[0] == 'P'):
        row[0] = ''
        break

    self.playBtn.get_children()[0].set_from_icon_name('media-playback-start', Gtk.IconSize.BUTTON)
    # only enable the transport buttons if mpv is running
    if(self.mpvRunning == True):
      self.playBtn.set_sensitive(True)
    self.stopBtn.set_sensitive(False)

    self.mediaPlaying = None
    self.playlistPlaying = None

  def deleteEntries(self, obj):
    playlist = None
    if(self.playlist1Label.get_text() == obj['playlist']):
      playlist = self.playlist1ListStore
    elif(self.playlist2Label.get_text() == obj['playlist']):
      playlist = self.playlist2ListStore
    
    if(playlist != None):
      for entry in obj['entries']:
        playlist.remove(playlist.get_iter(Gtk.TreePath.new_from_indices([entry])))

  def haveOpts(self):
    self.mpvOptsBtn.set_sensitive(True)    

  def __init__(self, client):
    Gtk.Window.__init__(self, title="MPV-VJ 2")
    self.client = client
    self.mediaPlaying = None
    self.playlistPlaying = None
    self.mpvRunning = False

    self.playlistsView = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    self.playlistsBar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    self.addBtn = Gtk.Button()
    self.addBtn.add(Gtk.Image.new_from_icon_name('list-add', Gtk.IconSize.BUTTON))
    self.addBtn.set_sensitive(False)
    self.playlistsBar.pack_start(self.addBtn, False, False, 0)
    self.playlistsListStore = Gtk.ListStore(str, str, str, str)
    self.playlistsList = Gtk.TreeView.new_with_model(self.playlistsListStore)
    self.playlistsStateColumn = Gtk.TreeViewColumn("S", Gtk.CellRendererText(), text=0)
    self.playlistsStateColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlistsList.append_column(self.playlistsStateColumn)
    self.playlistsNameColumn = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=1)
    self.playlistsNameColumn.set_resizable(True)
    self.playlistsNameColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlistsList.append_column(self.playlistsNameColumn)
    self.playlistsRandomColumn = Gtk.TreeViewColumn("R", Gtk.CellRendererText(), text=2)
    self.playlistsRandomColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlistsList.append_column(self.playlistsRandomColumn)
    self.playlistsLoopingColumn = Gtk.TreeViewColumn("L", Gtk.CellRendererText(), text=3)
    self.playlistsLoopingColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlistsList.append_column(self.playlistsLoopingColumn)
    self.playlistsList.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    self.playlistsList.set_search_column(1)
    self.playlistsList.set_enable_search(False)
    self.playlistsList.set_sensitive(False)
    self.playlistsView.pack_start(self.playlistsBar, False, False, 0)
    scroll = Gtk.ScrolledWindow()
    scroll.add(self.playlistsList)
    self.playlistsView.pack_start(scroll, True, True, 0)    
    self.addBtn.connect('clicked', self.newPlaylist)
    self.playlistsList.connect('key-press-event', self.playlistItemActions)

    self.playlist1View = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    self.playlist1Bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    self.addUrl1Btn = Gtk.Button()
    self.addUrl1Btn.add(Gtk.Image.new_from_icon_name('list-add', Gtk.IconSize.BUTTON))
    self.addUrl1Btn.set_sensitive(False)
    self.playlist1Bar.pack_start(self.addUrl1Btn, False, False, 0)
    self.addFiles1Btn = Gtk.Button()
    self.addFiles1Btn.add(Gtk.Image.new_from_icon_name('document-open', Gtk.IconSize.BUTTON))
    self.addFiles1Btn.set_sensitive(False)
    self.playlist1Bar.pack_start(self.addFiles1Btn, False, False, 0)
    self.playlist1ListStore = Gtk.ListStore(str, str, str)
    self.playlist1List = Gtk.TreeView.new_with_model(self.playlist1ListStore)
    self.playlist1StateColumn = Gtk.TreeViewColumn("S", Gtk.CellRendererText(), text=0)
    self.playlist1StateColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlist1List.append_column(self.playlist1StateColumn)
    self.playlist1NameColumn = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=1)
    self.playlist1NameColumn.set_resizable(True)
    self.playlist1NameColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlist1List.append_column(self.playlist1NameColumn)
    self.playlist1PlayedColumn = Gtk.TreeViewColumn("P", Gtk.CellRendererText(), text=2)
    self.playlist1PlayedColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlist1List.append_column(self.playlist1PlayedColumn)
    self.playlist1List.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    self.playlist1List.set_search_column(1)
    self.playlist1List.set_enable_search(False)
    self.playlist1List.set_sensitive(False)
    self.playlist1Label = Gtk.Label()
    self.playlist1View.pack_start(self.playlist1Bar, False, False, 0)
    self.playlist1View.pack_start(self.playlist1Label, False, False, 0)
    scroll = Gtk.ScrolledWindow()
    scroll.add(self.playlist1List)
    self.playlist1View.pack_start(scroll, True, True, 0)    
    self.addUrl1Btn.connect('clicked', self.addURL, self.playlist1Label)
    self.playlist1View.connect('key-press-event', self.playlistActions, self.playlist1Label)
    self.playlist1View.connect('button-press-event', self.playlistActions, self.playlist1Label)

    self.playlist2View = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    self.playlist2Bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    self.addUrl2Btn = Gtk.Button()
    self.addUrl2Btn.add(Gtk.Image.new_from_icon_name('list-add', Gtk.IconSize.BUTTON))
    self.addUrl2Btn.set_sensitive(False)
    self.playlist2Bar.pack_start(self.addUrl2Btn, False, False, 0)
    self.addFiles2Btn = Gtk.Button()
    self.addFiles2Btn.add(Gtk.Image.new_from_icon_name('document-open', Gtk.IconSize.BUTTON))
    self.addFiles2Btn.set_sensitive(False)
    self.playlist2Bar.pack_start(self.addFiles2Btn, False, False, 0)
    self.playlist2ListStore = Gtk.ListStore(str, str, str)
    self.playlist2List = Gtk.TreeView.new_with_model(self.playlist2ListStore)
    self.playlist2StateColumn = Gtk.TreeViewColumn("S", Gtk.CellRendererText(), text=0)
    self.playlist2StateColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlist2List.append_column(self.playlist2StateColumn)
    self.playlist2NameColumn = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=1)
    self.playlist2NameColumn.set_resizable(True)
    self.playlist2NameColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlist2List.append_column(self.playlist2NameColumn)
    self.playlist2PlayedColumn = Gtk.TreeViewColumn("P", Gtk.CellRendererText(), text=2)
    self.playlist2PlayedColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.playlist2List.append_column(self.playlist2PlayedColumn)
    self.playlist2List.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    self.playlist2List.set_search_column(1)
    self.playlist2List.set_enable_search(False)
    self.playlist2List.set_sensitive(False)
    self.playlist2Label = Gtk.Label()
    self.playlist2View.pack_start(self.playlist2Bar, False, False, 0)
    self.playlist2View.pack_start(self.playlist2Label, False, False, 0)
    scroll = Gtk.ScrolledWindow()
    scroll.add(self.playlist2List)
    self.playlist2View.pack_start(scroll, True, True, 0)    
    self.addUrl2Btn.connect('clicked', self.addURL, self.playlist2Label)
    self.playlist2View.connect('key-press-event', self.playlistActions, self.playlist2Label)
    self.playlist2View.connect('button-press-event', self.playlistActions, self.playlist2Label)

    self.plViewsBox = Gtk.HPaned()
    self.plViewsBox.pack1(self.playlist1View, True, False)
    self.plViewsBox.pack2(self.playlist2View, True, False)

    self.viewBox = Gtk.HPaned()
    self.viewBox.pack1(self.playlistsView, True, False)
    self.viewBox.pack2(self.plViewsBox, True, False)
    self.viewBox.set_position(200)

    self.logView = Gtk.TextView()
    self.logView.set_editable(False)
    self.logView.set_monospace(True)

    self.contentBox = Gtk.VPaned()
    self.contentBox.pack1(self.viewBox, False, False)
    scroll = Gtk.ScrolledWindow()
    scroll.add(self.logView)
    self.contentBox.pack2(scroll, False, True)
    self.contentBox.set_position(800)

    self.toolBar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    self.newBtn = Gtk.Button()
    self.newBtn.add(Gtk.Image.new_from_icon_name('document-new', Gtk.IconSize.BUTTON))
    self.newBtn.set_sensitive(False)
    self.toolBar.pack_start(self.newBtn, False, False, 0)
    self.loadBtn = Gtk.Button()
    self.loadBtn.add(Gtk.Image.new_from_icon_name('document-open', Gtk.IconSize.BUTTON))
    self.loadBtn.set_sensitive(False)
    self.toolBar.pack_start(self.loadBtn, False, False, 0)
    self.saveBtn = Gtk.Button()
    self.saveBtn.add(Gtk.Image.new_from_icon_name('document-save', Gtk.IconSize.BUTTON))
    self.saveBtn.set_sensitive(False)
    self.toolBar.pack_start(self.saveBtn, False, False, 0)
    self.settingsBtn = Gtk.Button()
    self.settingsBtn.add(Gtk.Image.new_from_icon_name('emblem-system', Gtk.IconSize.BUTTON))
    self.toolBar.pack_start(self.settingsBtn, False, False, 0)
    self.connectBtn = Gtk.Button()
    self.connectBtn.add(Gtk.Image.new_from_icon_name('network-idle', Gtk.IconSize.BUTTON))
    self.toolBar.pack_start(self.connectBtn, False, False, 0)
    self.mpvBtn = Gtk.Button()
    self.mpvBtn.add(Gtk.Image.new_from_icon_name('go-up', Gtk.IconSize.BUTTON))
    self.mpvBtn.set_sensitive(False)
    self.toolBar.pack_start(self.mpvBtn, False, False, 0)
    self.mpvOptsBtn = Gtk.Button()
    self.mpvOptsBtn.add(Gtk.Image.new_from_icon_name('text-x-generic', Gtk.IconSize.BUTTON))
    self.mpvOptsBtn.set_sensitive(False)
    self.toolBar.pack_start(self.mpvOptsBtn, False, False, 0)
    self.playBtn = Gtk.Button()
    self.playBtn.add(Gtk.Image.new_from_icon_name('media-playback-start', Gtk.IconSize.BUTTON))
    self.playBtn.set_sensitive(False)
    self.toolBar.pack_start(self.playBtn, False, False, 0)
    self.stopBtn = Gtk.Button()
    self.stopBtn.add(Gtk.Image.new_from_icon_name('media-playback-stop', Gtk.IconSize.BUTTON))
    self.stopBtn.set_sensitive(False)
    self.toolBar.pack_start(self.stopBtn, False, False, 0)

    self.settingsBtn.connect('clicked', self.editSettings)
    self.mpvOptsBtn.connect('clicked', self.editMpvOpts)
    self.playBtn.connect('clicked', self.playMedia)
    self.stopBtn.connect('clicked', self.stopMedia)
    self.connectHandlerID = self.connectBtn.connect('clicked', self.connectClient)
    self.mpvHandlerID = None

    self.mainBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    self.mainBox.pack_start(self.toolBar, False, False, 0)
    self.mainBox.pack_start(self.contentBox, True, True, 0)
    
    self.add(self.mainBox)

    self.resize(1000, 1000)
