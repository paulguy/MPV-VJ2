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


import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Gdk

import PromptDialog
import SettingsDialog
import FileListDialog


class MainWindow(Gtk.Window):
    def getListBoxLabel(text):
        label = Gtk.Label(text)
        label.set_halign(Gtk.Align.START)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.show()
        return label

    def newPlaylistResponse(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.client.newPlaylist(dialog.get_text())
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def newPlaylist(self, button):
        dialog = PromptDialog.PromptDialog(self, "New Playlist")
        dialog.connect('response', self.newPlaylistResponse)
        dialog.show_all()

    def editSettingsResponse(self, dialog, response):
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def editSettings(self, button):
        settingsDialog = SettingsDialog.SettingsDialog(self, self.client.settings)
        settingsDialog.connect('response', self.editSettingsResponse)
        settingsDialog.show_all()

    def editMpvOptsResponse(self, dialog, response):
        self.client.sendOpts()
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def editMpvOpts(self, button):
        settingsDialog = SettingsDialog.SettingsDialog(self, self.client.getOpts(), add=True)
        settingsDialog.connect('response', self.editMpvOptsResponse)
        settingsDialog.show_all()

    def connectClient(self, button):
        self.client.connect()

    def setSensitive(self, sensitive):
        if not sensitive:
            self.clearState()
            self.mpvBtn.set_sensitive(False)
            self.playBtn.set_sensitive(False)
            self.stopBtn.set_sensitive(False)
            self.mpvOptsBtn.set_sensitive(False)
            if self.mpvHandlerID is not None:
                self.mpvBtn.disconnect(self.mpvHandlerID)
                self.mpvHandlerID = None
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

        if name is not None:
            playlistView.get_children()[1].set_text(name)

            current, entries = self.client.getPlaylistEntries(name)
            for entry in enumerate(entries):
                state = ''
                played = 'N'
                if entry[0] == current:
                    state = 'C'
                if self.playlistPlaying == name:
                    if entry[0] == self.mediaPlaying:
                        state = 'P'
                try:
                    if entry[1]['played']:
                        played = 'Y'
                except KeyError:
                    pass
                filePath, fileName = os.path.split(entry[1]['name'])
                playlistStore.append((state, fileName, played))
        else:
            playlistView.get_children()[1].set_text("")

    def playlistListActivated(self, playlistList, row, column):
        model, rows = playlistList.get_selection().get_selected_rows()

        if column.get_title() == "R":
            self.client.toggleRandom(model[rows[0].get_indices()[0]][1])
        elif column.get_title() == "L":
            self.client.toggleLooping(model[rows[0].get_indices()[0]][1])

    def playlistItemActions(self, playlistList, event):
        model, rows = playlistList.get_selection().get_selected_rows()

        if len(rows) == 0:
            return False

        if (event.type == Gdk.EventType.KEY_PRESS):
            if (event.keyval == Gdk.KEY_l):
                if (len(rows) == 1):
                    pl = model[rows[0].get_indices()[0]][1]
                    if self.playlist2Label.get_text() == pl:
                        return False
                    self.refreshPlaylistView(self.playlist1View, pl)
            elif event.keyval == Gdk.KEY_r:
                if len(rows) == 1:
                    pl = model[rows[0].get_indices()[0]][1]
                    if self.playlist1Label.get_text() == pl:
                        return False
                    self.refreshPlaylistView(self.playlist2View, pl)
            elif event.keyval == Gdk.KEY_c:
                if len(rows) == 1:
                    pl = model[rows[0].get_indices()[0]][1]
                    self.client.cuePlaylist(pl)
            elif event.keyval == Gdk.KEY_Delete:
                pls = []
                for row in rows:
                    pls.append(model[row.get_indices()[0]][1])
                self.client.deletePlaylists(pls)
        return False

    def playlistActivated(self, playlist, row, column, label):
        idx = row.get_indices()[0]
        if column.get_title() == "P":
            pl = label.get_text()
            self.client.togglePlayed(pl, idx)
        else:
            pl = label.get_text()
            self.client.cuePlaylist(pl)
            self.client.cueEntry(pl, row.get_indices()[0])
            self.client.playMedia()

    def playlistActions(self, playlist, event, label):
        model, rows = playlist.get_selection().get_selected_rows()

        if len(rows) == 0:
            return False

        if event.type == Gdk.EventType.KEY_PRESS:
            if event.keyval == Gdk.KEY_c:
                if len(rows) == 1:
                    pl = label.get_text()
                    self.client.cueEntry(pl, rows[0].get_indices()[0])
            if event.keyval == Gdk.KEY_Delete:
                pl = label.get_text()
                items = []
                for row in rows:
                    items.append(row.get_indices()[0])
                self.client.deleteEntries(pl, items)
        return False

    def addURLResponse(self, dialog, response, playlistLabel):
        if response == Gtk.ResponseType.OK:
            self.client.addEntries(playlistLabel.get_text(), [dialog.get_text()])
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def addURL(self, button, playlistLabel):
        if playlistLabel.get_text() == '':
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

    def newSession(self, button):
        self.client.newSession()

    def saveSessionResponse(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            self.client.saveFile(dialog.get_filename())
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def saveSession(self, button):
        dialog = Gtk.FileChooserDialog("Save File",
                                       self,
                                       Gtk.FileChooserAction.SAVE)
        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Save", Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.connect('response', self.saveSessionResponse)
        dialog.show_all()

    def loadSessionResponse(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            self.client.loadFile(dialog.get_filename())
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def loadSession(self, button):
        dialog = Gtk.FileChooserDialog("Load File",
                                       self,
                                       Gtk.FileChooserAction.OPEN)
        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Load", Gtk.ResponseType.ACCEPT)
        dialog.connect('response', self.loadSessionResponse)
        dialog.show_all()

    def addFiles(self, button, playlistLabel):
        if playlistLabel.get_text() == '':
            return
        self.client.getFileList("", playlistLabel.get_text())

    # event inputs

    def newPlaylists(self, obj):
        for item in obj['playlists']:
            random = 'N'
            loop = 'N'
            try:
                if item['random']:
                    random = 'Y'
            except KeyError:
                pass
            try:
                if item['loop']:
                    loop = 'Y'
            except KeyError:
                pass
            self.playlistsListStore.append(('', item['name'], random, loop))

    def deletePlaylists(self, obj):
        for pl in obj['playlists']:
            for row in self.playlistsListStore:
                if row[1] == pl:
                    if self.playlist1Label.get_text() == pl:
                        self.refreshPlaylistView(self.playlist1View, None)
                    elif self.playlist2Label.get_text() == pl:
                        self.refreshPlaylistView(self.playlist2View, None)
                    self.playlistsListStore.remove(row.iter)

    def setCurrentPlaylist(self, obj):
        for row in self.playlistsListStore:
            if obj['playlist'] == row[1]:
                row[0] = 'C'
            elif row[0] == 'C':
                row[0] = ''

    def cueItem(self, obj):
        playlist = None
        if self.playlist1Label.get_text() == obj['playlist']:
            playlist = self.playlist1ListStore
        elif self.playlist2Label.get_text() == obj['playlist']:
            playlist = self.playlist2ListStore

        if playlist is not None:
            for row in enumerate(playlist):
                if row[1][0] == 'C' and playlist[0] != obj['item']:
                    row[1][0] = ''
                    break

            playlist[obj['item']][0] = 'C'

    def addEntries(self, obj):
        playlist = None
        if self.playlist1Label.get_text() == obj['playlist']:
            playlist = self.playlist1ListStore
        elif self.playlist2Label.get_text() == obj['playlist']:
            playlist = self.playlist2ListStore

        if playlist is not None:
            i = None
            try:
                i = playlist.get_iter(Gtk.TreePath.new_from_indices([obj['location']]))
            except KeyError:
                pass
            for entry in obj['entries']:
                played = 'N'
                try:
                    if entry['played']:
                        played = 'Y'
                except KeyError:
                    pass
                filePath, fileName = os.path.split(entry['name'])
                if i is None:
                    playlist.append(('', fileName, played))
                else:
                    playlist.insert_before(i, ('', fileName, played))
                    i = playlist.iter_next(i)

    def clientConnected(self):
        self.connectBtn.get_children()[0].set_from_icon_name('network-offline', Gtk.IconSize.BUTTON)
        self.connectBtn.disconnect(self.connectHandlerID)
        self.connectHandlerID = self.connectBtn.connect('clicked', self.disconnectClient)
        self.setSensitive(True)

    def clientDisconnected(self):
        if self.is_visible():  # avoid exception on close when still connected
            self.connectBtn.get_children()[0].set_from_icon_name('network-idle', Gtk.IconSize.BUTTON)
            self.connectBtn.disconnect(self.connectHandlerID)
            self.connectHandlerID = self.connectBtn.connect('clicked', self.connectClient)
            self.setSensitive(False)

    def MPVStarted(self):
        self.mpvBtn.get_children()[0].set_from_icon_name('go-down', Gtk.IconSize.BUTTON)
        if self.mpvHandlerID is not None:
            self.mpvBtn.disconnect(self.mpvHandlerID)
        self.mpvHandlerID = self.mpvBtn.connect('clicked', self.stopMPV)
        self.mpvBtn.set_sensitive(True)

        # make transport buttons sensitive
        if self.mediaPlaying is not None:
            self.playBtn.get_children()[0].set_from_icon_name('media-skip-forward', Gtk.IconSize.BUTTON)
            self.stopBtn.set_sensitive(True)
        self.playBtn.set_sensitive(True)

        self.mpvRunning = True

    def MPVStopped(self):
        self.mpvBtn.get_children()[0].set_from_icon_name('go-up', Gtk.IconSize.BUTTON)
        if self.mpvHandlerID is not None:
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
        if self.playlist1Label.get_text() == obj['playlist']:
            playlist = self.playlist1ListStore
        elif self.playlist2Label.get_text() == obj['playlist']:
            playlist = self.playlist2ListStore

        if playlist is not None:
            for row in playlist:
                if row[0] == 'P':
                    row[0] = ''

            playlist[obj['item']][0] = 'P'

        self.playBtn.get_children()[0].set_from_icon_name('media-skip-forward', Gtk.IconSize.BUTTON)
        self.playBtn.set_sensitive(True)
        self.stopBtn.set_sensitive(True)

        self.mediaPlaying = obj['item']
        self.playlistPlaying = obj['playlist']

    def stopped(self):
        for row in self.playlist1ListStore:
            if row[0] == 'P':
                row[0] = ''
                break
        for row in self.playlist2ListStore:
            if row[0] == 'P':
                row[0] = ''
                break

        self.playBtn.get_children()[0].set_from_icon_name('media-playback-start', Gtk.IconSize.BUTTON)
        # only enable the transport buttons if mpv is running
        if self.mpvRunning:
            self.playBtn.set_sensitive(True)
        self.stopBtn.set_sensitive(False)

        self.mediaPlaying = None
        self.playlistPlaying = None

    def deleteEntries(self, obj):
        playlist = None
        if self.playlist1Label.get_text() == obj['playlist']:
            playlist = self.playlist1ListStore
        elif self.playlist2Label.get_text() == obj['playlist']:
            playlist = self.playlist2ListStore

        if playlist is not None:
            for entry in obj['entries']:
                playlist.remove(playlist.get_iter(Gtk.TreePath.new_from_indices([entry])))

    def haveOpts(self):
        self.mpvOptsBtn.set_sensitive(True)

    def clearState(self):
        self.playlistsListStore.clear()
        self.playlist1ListStore.clear()
        self.playlist2ListStore.clear()
        self.playlist1Label.set_text("")
        self.playlist2Label.set_text("")

    def setPlayed(self, obj):
        playlist = None
        if (self.playlist1Label.get_text() == obj['playlist']):
            playlist = self.playlist1ListStore
        elif (self.playlist2Label.get_text() == obj['playlist']):
            playlist = self.playlist2ListStore

        if playlist is not None:
            if obj['value']:
                playlist[obj['item']][2] = 'Y'
            else:
                playlist[obj['item']][2] = 'N'

    def setRandom(self, obj):
        plRow = None
        for row in self.playlistsListStore:
            if row[1] == obj['playlist']:
                plRow = row
                break

        if obj['value']:
            plRow[2] = 'Y'
        else:
            plRow[2] = 'N'

    def setLooping(self, obj):
        plRow = None
        for row in self.playlistsListStore:
            if row[1] == obj['playlist']:
                plRow = row
                break

        if obj['value']:
            plRow[3] = 'Y'
        else:
            plRow[3] = 'N'

    def listFilesResponse(self, dialog, response, playlist):
        if response == Gtk.ResponseType.ACCEPT:
            itemType, items = dialog.get_selection()
            if itemType == "D":
                if items == "..":
                    filePath, fileName = os.path.split(dialog.get_path())
                    self.client.getFileList(os.path.join(filePath), playlist)
                else:
                    self.client.getFileList(os.path.join(dialog.get_path(), items[0]), playlist)
            else:
                for item in enumerate(items):
                    items[item[0]] = os.path.join(dialog.get_path(), item[1])
                print(repr(items))
                self.client.addEntries(playlist, items)
        if response != Gtk.ResponseType.DELETE_EVENT:
            dialog.destroy()

    def listFiles(self, obj):
        if 'path' not in obj:
            return "No 'path'."
        if type(obj['path']) != str:
            return "'path' is not a string."
        if 'playlist' not in obj:
            return "No 'playlist'."
        if type(obj['playlist']) != str:
            return "'playlist' is not a string."
        if 'dirs' not in obj:
            return "No 'dirs'."
        if type(obj['dirs']) != list:
            return "'dirs' is not a list."
        for item in obj['dirs']:
            if type(item) != str:
                return "'dirs' item is not a string."
        if 'files' not in obj:
            return "No 'files'."
        if type(obj['files']) != list:
            return "'files' is not a list."
        for item in obj['files']:
            if type(item) != str:
                return "'files' item is not a string."
        dialog = FileListDialog.FileListDialog(self, obj['path'], obj['dirs'], obj['files'])
        dialog.connect('response', self.listFilesResponse, obj['playlist'])
        dialog.show_all()

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
        self.playlistsList.connect('row-activated', self.playlistListActivated)

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
        self.addFiles1Btn.connect('clicked', self.addFiles, self.playlist1Label)
        self.playlist1List.connect('key-press-event', self.playlistActions, self.playlist1Label)
        self.playlist1List.connect('row-activated', self.playlistActivated, self.playlist1Label)

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
        self.addFiles2Btn.connect('clicked', self.addFiles, self.playlist2Label)
        self.playlist2List.connect('key-press-event', self.playlistActions, self.playlist2Label)
        self.playlist2List.connect('row-activated', self.playlistActivated, self.playlist2Label)

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

        self.newBtn.connect('clicked', self.newSession)
        self.saveBtn.connect('clicked', self.saveSession)
        self.loadBtn.connect('clicked', self.loadSession)
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
