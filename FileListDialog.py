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


import os.path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk

class FileListDialog(Gtk.Dialog):
  def get_selection(self):
    return(self.selection)

  def get_path(self):
    return(self.path)

  def closeAlert(self, dialog, response):
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()    

  def setSelection(self):
    model, rows = self.listView.get_selection().get_selected_rows()
    
    self.selection = ("F", [])
    for row in rows:
      if(model[row.get_indices()[0]][1] == "D"):
        alertBox = Gtk.MessageDialog(parent=dialog,
                                     flags=Gtk.DialogFlags.MODAL,
                                     type=Gtk.MessageType.ERROR,
                                     buttons=Gtk.ButtonsType.OK,
                                     message_format="Only multiple files may be selected.")
        alertBox.connect('response', self.closeAlert)
        alertBox.show_all()
        return
      self.selection[1].append(self.listStore[row.get_indices()[0]][0])
    self.emit('response', Gtk.ResponseType.ACCEPT)

  def keyPress(self, listView, event):
    if(event.type == Gdk.EventType.KEY_PRESS):
      if(event.keyval == Gdk.KEY_Return):
        self.setSelection()
        return(True) #Don't let enter fall through
    return(False)

  def selectEntry(self, listView, row, column):
    self.selection = (self.listStore[row.get_indices()[0]][1], [self.listStore[row.get_indices()[0]][0]])
    self.emit('response', Gtk.ResponseType.ACCEPT)

  def returnFiles(self, button):
    self.setSelection()

  def goUp(self, button):
    self.selection = ("D", "..")
    self.emit('response', Gtk.ResponseType.ACCEPT)    

  def __init__(self, lastWindow, path, dirs, files):
    Gtk.Dialog.__init__(self, title=path)

    self.set_modal(True)
    self.set_transient_for(lastWindow)

    self.path = path

    self.listStore = Gtk.ListStore(str, str)
    for d in dirs:
      self.listStore.append((d, "D"))
    for f in files:
      self.listStore.append((f, "F"))

    self.listView = Gtk.TreeView.new_with_model(self.listStore)
    self.nameColumn = Gtk.TreeViewColumn("Name", Gtk.CellRendererText(), text=0)
    self.nameColumn.set_resizable(True)
    self.nameColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.listView.append_column(self.nameColumn)
    self.typeColumn = Gtk.TreeViewColumn("T", Gtk.CellRendererText(), text=1)
    self.typeColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.listView.append_column(self.typeColumn)
    self.listView.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    self.listView.set_search_column(0)
    self.listView.set_enable_search(True)
    self.listView.connect('key-press-event', self.keyPress)
    self.listView.connect('row-activated', self.selectEntry)

    self.buttonBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    self.addBtn = Gtk.Button()
    self.addBtn.add(Gtk.Image.new_from_icon_name('list-add', Gtk.IconSize.BUTTON))
    self.addBtn.connect('clicked', self.returnFiles)
    self.buttonBox.pack_start(self.addBtn, False, False, 0)
    self.upBtn = Gtk.Button()
    self.upBtn.add(Gtk.Image.new_from_icon_name('go-up', Gtk.IconSize.BUTTON))
    self.upBtn.connect('clicked', self.goUp)
    self.buttonBox.pack_start(self.upBtn, False, False, 0)

    self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    scroll = Gtk.ScrolledWindow()
    scroll.add(self.listView)
    self.box.pack_start(scroll, True, True, 0)
    self.box.pack_start(self.buttonBox, False, False, 0)
    self.get_content_area().pack_start(self.box, True, True, 0)
    
    self.add_button("Close", Gtk.ResponseType.CLOSE)

    self.resize(700, 700)
