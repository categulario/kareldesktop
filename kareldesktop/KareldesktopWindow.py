# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('kareldesktop')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('kareldesktop')

from kareldesktop_lib import Window
from kareldesktop.AboutKareldesktopDialog import AboutKareldesktopDialog
from kareldesktop.PreferencesKareldesktopDialog import PreferencesKareldesktopDialog

# See kareldesktop_lib.Window.py for more details about how this class works
class KareldesktopWindow(Window):
    __gtype_name__ = "KareldesktopWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(KareldesktopWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutKareldesktopDialog
        self.PreferencesDialog = PreferencesKareldesktopDialog

        # Code for other initialization actions should be added here.

