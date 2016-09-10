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
from gi.repository import Gdk
from gi.repository import Pango

import PromptDialog

class SettingsDialog(Gtk.Dialog):
  def closeAlert(self, dialog, response):
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()    

  def editKeyResponse(self, dialog, response, key):
    if(response == Gtk.ResponseType.OK):
      if(dialog.get_text() in self.options):
        alertBox = Gtk.MessageDialog(parent=dialog,
                                     flags=Gtk.DialogFlags.MODAL,
                                     type=Gtk.MessageType.ERROR,
                                     buttons=Gtk.ButtonsType.OK,
                                     message_format="Key already exists.")
        alertBox.connect('response', self.closeAlert)
        alertBox.show_all()
      else:
        newKey = dialog.get_text()
        value = self.options[key]
        del self.options[key]
        self.options[newKey] = value

        for row in self.listStore:
          if(row[0] == key):
            row[0] = newKey
            break
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()

  def editValueResponse(self, dialog, response, key):
    value = dialog.get_text()
    if(response == Gtk.ResponseType.OK):
      self.options[key] = value
      for row in self.listStore:
        if(row[0] == key):
          row[1] = value
          break
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()

  def editEntry(self, listView, row, column):
    #i = self.listStore.get_iter(row)
    #key = self.listStore.get_value(i, 0)
    key = self.listStore[0][row.get_indices()[0]]
    if(self.add == True and column.get_title() == "Key"):
      editDialog = PromptDialog.PromptDialog(self, "Edit Key", key)
      editDialog.connect('response', self.editKeyResponse, key)
      editDialog.show_all()
    else:
      editDialog = PromptDialog.PromptDialog(self, "Edit Value", self.options[key])
      editDialog.connect('response', self.editValueResponse, key)
      editDialog.show_all()

  def addKeyResponse(self, dialog, response):
    key = dialog.get_text()
    if(response == Gtk.ResponseType.OK):
      self.options[key] = ""
      i = self.listStore.get_iter_first()
      self.listStore.insert_before(i, (key, ""))
    if(response != Gtk.ResponseType.DELETE_EVENT):
      dialog.destroy()

  def addKey(self, button):
    editDialog = PromptDialog.PromptDialog(self, "Add Key")
    editDialog.connect('response', self.addKeyResponse)
    editDialog.show_all()

  def delKey(self, button):
    row, column = self.listView.get_cursor()
    #i = self.listStore.get_iter(row)
    #key = self.listStore.get_value(i, 0)
    key = self.listStore[0][row.get_indices()[0]]
    del self.options[key]
    self.listStore.remove(i)

  def __init__(self, lastWindow, options, add=False):
    Gtk.Dialog.__init__(self, title="Settings")

    self.add = add

    self.set_modal(True)
    self.set_transient_for(lastWindow)

    if(type(options) != dict):
      raise TypeError
    if(type(add) != bool):
      raise TypeError
    self.options = options

    self.listStore = Gtk.ListStore(str, str)
    for key in self.options.keys():
      if(type(key) != str or type(self.options[key]) != str):
        raise TypeError
      self.listStore.append((key, self.options[key]))

    self.listView = Gtk.TreeView.new_with_model(self.listStore)
    self.keyColumn = Gtk.TreeViewColumn("Key", Gtk.CellRendererText(), text=0)
    self.keyColumn.set_resizable(True)
    self.keyColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.listView.append_column(self.keyColumn)
    self.valueColumn = Gtk.TreeViewColumn("Value", Gtk.CellRendererText(), text=1)
    self.valueColumn.set_resizable(True)
    self.valueColumn.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    self.listView.append_column(self.valueColumn)
    self.listView.set_search_column(0)
    self.listView.set_enable_search(True)
    self.listView.connect('row-activated', self.editEntry)

    if(self.add == True):
      self.buttonBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
      self.addBtn = Gtk.Button()
      self.addBtn.add(Gtk.Image.new_from_icon_name('list-add', Gtk.IconSize.BUTTON))
      self.addBtn.connect('clicked', self.addKey)
      self.delBtn = Gtk.Button()
      self.delBtn.add(Gtk.Image.new_from_icon_name('list-remove', Gtk.IconSize.BUTTON))
      self.delBtn.connect('clicked', self.delKey)
      self.buttonBox.pack_start(self.addBtn, False, False, 0)
      self.buttonBox.pack_start(self.delBtn, False, False, 0)

      self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
      scroll = Gtk.ScrolledWindow()
      scroll.add(self.listView)
      self.box.pack_start(scroll, True, True, 0)
      self.box.pack_start(self.buttonBox, False, False, 0)
      self.get_content_area().pack_start(self.box, True, True, 0)
    else:
      scroll = Gtk.ScrolledWindow()
      scroll.add(self.listView)
      self.get_content_area().pack_start(scroll, True, True, 0)
    self.add_button("Close", Gtk.ResponseType.CLOSE)

    self.resize(200, 200)
