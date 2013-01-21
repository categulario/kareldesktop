# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext, math
from gettext import gettext as _
gettext.textdomain('kareldesktop')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('kareldesktop')

from kareldesktop_lib import Window
from kareldesktop_lib.karel.kworld import kworld
from kareldesktop.AboutKareldesktopDialog import AboutKareldesktopDialog
from kareldesktop.PreferencesKareldesktopDialog import PreferencesKareldesktopDialog

class coordenada(object):
    """una simple coordenada"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

# See kareldesktop_lib.Window.py for more details about how this class works
class KareldesktopWindow(Window):
    __gtype_name__ = "KareldesktopWindow"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(KareldesktopWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutKareldesktopDialog
        self.PreferencesDialog = PreferencesKareldesktopDialog

        # Code for other initialization actions should be added here.

    def dibuja_mundo(self, dwarea, context):
        rect = dwarea.get_allocation()
        #x = rect.x + rect.width / 2
        #y = rect.y + rect.height / 2

        #hallamos el radio
        #radius = min(rect.width / 2, rect.height / 2) - 20

        #Dibujamos un arco
        #context.arc(x, y, radius, 0,(2 * math.pi))

        context.rectangle(0, 0, rect.width, rect.height)
        context.set_source_rgb(0.59, 0.59, 0.59)
        context.fill_preserve()

        context.clip()

        tamanio_lienzo = coordenada(rect.width-20, rect.height-20)

        context.rectangle(20, 0, tamanio_lienzo.x, tamanio_lienzo.y)
        context.set_source_rgb(1, 1, 1)
        context.fill_preserve()

        context.clip()

        origen = coordenada(20, rect.height-40) #Coordenada para dibujar la primera casilla

        itera_columnas = int(tamanio_lienzo.x/20 + math.ceil((tamanio_lienzo.x%20)/20.))
        itera_filas = int(tamanio_lienzo.y/20 + math.ceil((tamanio_lienzo.y%20)/20.))
        for i in xrange(itera_columnas):
            for j in xrange(itera_filas):
                #context.save()
                x = origen.x+20*i
                y = origen.y-20*j
                context.rectangle(x-2, y+16, 6, 6)
                context.set_source_rgb(.4, .4, .4)
                context.fill_preserve()
        #Dibujar a Karel
        context.move_to ( origen.x, origen.y);
        context.line_to ( 230.4, 230.4);
        context.rel_line_to ( -102.4, 0.0);
        context.curve_to ( 51.2, 230.4, 51.2, 128.0, 128.0, 128.0);
        context.close_path ();

        context.move_to ( 64.0, 25.6);
        context.rel_line_to ( 51.2, 51.2);
        context.rel_line_to ( -51.2, 51.2);
        context.rel_line_to ( -51.2, -51.2);
        context.close_path ();

        context.set_line_width ( 10.0);
        context.set_source_rgb ( 0, 0, 1);
        context.fill_preserve ();

    def mundo_click(self, a, event):
        """Maneja los clicks en el mundo"""
        print event.x, event.y

    def gtk_main_quit(self, componente):
        Gtk.main_quit()
