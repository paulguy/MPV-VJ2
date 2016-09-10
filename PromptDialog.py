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

class PromptDialog(Gtk.Dialog):
  def get_text(self):
    return(self.entry.get_buffer().get_text())

  def keyPressed(self, dialog, event):
    if(event.type == Gdk.EventType.KEY_PRESS):
      if(event.keyval == Gdk.KEY_Return):
        self.emit('response', Gtk.ResponseType.OK)
    return(False)

  def __init__(self, lastWindow, message, value=""):
    Gtk.Dialog.__init__(self, title="Prompt")
    
    self.set_modal(True)
    self.set_transient_for(lastWindow)
    
    self.label = Gtk.Label(message)
    self.entry = Gtk.Entry()
    self.entry.set_text(value)
    self.get_content_area().pack_start(self.label, True, True, 0)
    self.get_content_area().pack_start(self.entry, True, True, 0)
    
    self.add_button("OK", Gtk.ResponseType.OK)
    self.add_button("Cancel", Gtk.ResponseType.CANCEL)
    
    self.connect("key-press-event", self.keyPressed)
