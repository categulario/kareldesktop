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

        self.world = kworld()

        # Code for other initialization actions should be added here.

    def dibuja_mundo(self, dwarea, context):
        rect = dwarea.get_allocation()

        context.rectangle(0, 0, rect.width, rect.height)
        context.set_source_rgb(0.59, 0.59, 0.59)
        context.fill()

        tamanio_lienzo = coordenada(rect.width-20, rect.height-20)

        context.rectangle(20, 0, tamanio_lienzo.x, tamanio_lienzo.y)
        context.set_source_rgb(1, 1, 1)
        context.fill()

        origen = coordenada(20, rect.height-40) #Coordenada para dibujar la primera casilla

        itera_columnas = int(tamanio_lienzo.x/20 + math.ceil((tamanio_lienzo.x%20)/20.))
        itera_filas = int(tamanio_lienzo.y/20 + math.ceil((tamanio_lienzo.y%20)/20.))
        for i in xrange(itera_columnas): #Cuadrados de las esquinas, creo
            for j in xrange(itera_filas):
                x = origen.x+20*i
                y = origen.y-20*j
                context.rectangle(x-2, y+16, 6, 6)
                context.set_source_rgb(.4, .4, .4)
                context.fill()
        for i in xrange(itera_filas):
            context.select_font_face('monospace')
            context.set_font_size(14) # em-square height is 90 pixels
            context.move_to(2, rect.height-(25+i*20)) # move to point (x, y) = (10, 90)
            context.set_source_rgb(0, 0, 0)
            context.show_text(str(i+1))

        for i in xrange(itera_columnas):
            context.select_font_face('monospace')
            context.set_font_size(14) # em-square height is 90 pixels
            context.move_to(23+20*i, rect.height-5) # move to point (x, y) = (10, 90)
            context.set_source_rgb(0, 0, 0)
            context.show_text(str(i+1))

        #Dibujar a Karel
        context.set_source_rgb(0, 0, 1)
        if self.world.orientado_al('norte'):
            context.move_to ( origen.x, origen.y+8 );
            context.line_to ( origen.x+10, origen.y );
            context.line_to ( origen.x+20, origen.y+8 );
            context.line_to ( origen.x+15, origen.y+8 );
            context.line_to ( origen.x+15, origen.y+18 );
            context.line_to ( origen.x+5, origen.y+18 );
            context.line_to ( origen.x+5, origen.y+8 );
            context.close_path ();
            context.fill()

    def mundo_click(self, a, event):
        """Maneja los clicks en el mundo"""
        print event.x, event.y

    def gtk_main_quit(self, componente):
        Gtk.main_quit()
