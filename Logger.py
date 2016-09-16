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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Logger:
    def __init__(self, logWindow=None):
        self.logItems = []
        self.setWindow(logWindow)

    def addEntryToWindow(self, message):
        self.textBuffer.insert(self.textBuffer.get_end_iter(), message + "\n")

    def setWindow(self, logWindow):
        if logWindow is not None:
            self.textBuffer = Gtk.TextBuffer()
            for item in self.logItems:
                self.textBuffer.insert(self.textBuffer.get_end_iter(), item)
            logWindow.set_buffer(self.textBuffer)
        else:
            self.textBuffer = None

    def log(self, message):
        self.logItems.append(message)
        if self.textBuffer is not None:
            self.addEntryToWindow(message)
        print(message)
