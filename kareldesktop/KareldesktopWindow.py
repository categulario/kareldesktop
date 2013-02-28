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

        self.mundo = kworld()
        self.mundo.establece_karel(posicion=(2, 2), orientacion='este')
        self.mundo.conmuta_pared((2, 2), 'norte')
        self.mundo.conmuta_pared((2, 2), 'sur')
        self.mundo.conmuta_pared((2, 2), 'oeste')
        self.primera_fila = 1
        self.primera_columna = 1

        # Code for other initialization actions should be added here.

    def dibuja_mundo(self, dwarea, context):
        rect = dwarea.get_allocation()

        def dibuja_karel(origen):#Dibujar a Karel
            context.set_source_rgb(0, 0, 1)
            if self.mundo.orientado_al('norte'):
                context.move_to ( origen.x, origen.y+13 )
                context.line_to ( origen.x+15, origen.y )
                context.line_to ( origen.x+30, origen.y+13 )
                context.line_to ( origen.x+23, origen.y+13 )
                context.line_to ( origen.x+23, origen.y+27 )
                context.line_to ( origen.x+7, origen.y+27 )
                context.line_to ( origen.x+7, origen.y+13 )
                context.close_path ()
                context.fill()
            elif self.mundo.orientado_al('este'):
                context.move_to ( origen.x+3, origen.y+7 )
                context.line_to ( origen.x+17, origen.y+7 )
                context.line_to ( origen.x+17, origen.y )
                context.line_to ( origen.x+30, origen.y+15 )
                context.line_to ( origen.x+17, origen.y+30 )
                context.line_to ( origen.x+17, origen.y+23 )
                context.line_to ( origen.x+3, origen.y+23 )
                context.close_path ()
                context.fill()
            elif self.mundo.orientado_al('sur'):
                context.move_to ( origen.x+7, origen.y+3 )
                context.line_to ( origen.x+23, origen.y+3 )
                context.line_to ( origen.x+23, origen.y+17 )
                context.line_to ( origen.x+30, origen.y+17 )
                context.line_to ( origen.x+15, origen.y+30 )
                context.line_to ( origen.x, origen.y+17)
                context.line_to ( origen.x+7, origen.y+17)
                context.close_path()
                context.fill()
            elif self.mundo.orientado_al('oeste'):
                context.move_to( origen.x, origen.y+15 )
                context.line_to( origen.x+13, origen.y )
                context.line_to( origen.x+13, origen.y+7 )
                context.line_to( origen.x+27, origen.y+7 )
                context.line_to( origen.x+27, origen.y+23 )
                context.line_to( origen.x+13, origen.y+23 )
                context.line_to( origen.x+13, origen.y+30 )
                context.close_path()
                context.fill()

        context.rectangle(0, 0, rect.width, rect.height)
        context.set_source_rgb(0.59, 0.59, 0.59)
        context.fill()

        tamanio_lienzo = coordenada(rect.width-30, rect.height-30)
        self.tamanio_mundo = coordenada(rect.width, rect.height)

        context.rectangle(30, 0, tamanio_lienzo.x, tamanio_lienzo.y)
        context.set_source_rgb(1, 1, 1)
        context.fill()

        #IMPORTANTE
        origen = coordenada(30, rect.height-60) #Coordenada para dibujar la primera casilla

        self.num_columnas = int(tamanio_lienzo.x/30 + math.ceil((tamanio_lienzo.x%30)/30.))
        self.num_filas = int(tamanio_lienzo.y/30 + math.ceil((tamanio_lienzo.y%30)/30.))
        #Cuadrados de las esquinas
        for i in xrange(self.num_columnas):
            for j in xrange(self.num_filas):
                x = origen.x+30*i
                y = origen.y-30*j
                context.rectangle(x-2, y+26, 6, 6)
                context.set_source_rgb(.4, .4, .4)
                context.fill()

        #Dibujar las cosas que pertenecen al mundo
        num_fila = 1 #Posicion relativa a la pantalla
        num_columna = 1 #Posicion relativa a la pantalla
        for fila in xrange(self.primera_fila, self.primera_fila+self.num_filas):
            num_columna = 1
            for columna in xrange(self.primera_columna, self.primera_columna+self.num_columnas):
                casilla = self.mundo.obten_casilla((fila, columna)) #Casilla actual

                #Dibujar a karel
                if self.mundo.posicion_karel() == (fila, columna):
                    referencia = coordenada(origen.x+(num_columna-1)*30, origen.y-(num_fila-1)*30)
                    dibuja_karel(referencia)

                context.set_source_rgb(.1, .1, .1) #Casi negro para las paredes
                if 'este' in casilla['paredes']:
                    context.rectangle(origen.x+(num_columna-1)*30-1+30, origen.y-(num_fila-1)*30, 4, 30)
                    context.fill()
                if 'oeste' in casilla['paredes']:
                    context.rectangle(origen.x+(num_columna-1)*30-1, origen.y-(num_fila-1)*30, 4, 30)
                    context.fill()
                if 'sur' in casilla['paredes']:
                    context.rectangle(origen.x+(num_columna-1)*30+1, origen.y-(num_fila-1)*30+27, 30, 4)
                    context.fill()
                if 'norte' in casilla['paredes']:
                    context.rectangle(origen.x+(num_columna-1)*30+1, origen.y-(num_fila-1)*30+27-30, 30, 4)
                    context.fill()

                num_columna += 1
            num_fila += 1

        #Numeros de fila
        a = 1
        for i in xrange(self.primera_fila, self.primera_fila+self.num_filas): #Números de fila
            context.select_font_face('monospace')
            context.set_font_size(14) # em-square height is 90 pixels
            context.move_to(10, rect.height-(10+a*30)) # move to point (x, y) = (10, 90)
            context.set_source_rgb(0, 0, 0)
            context.show_text(str(i))
            a += 1

        #Numeros de colummna
        a = 1
        for i in xrange(self.primera_columna, self.primera_columna + self.num_columnas): #Números de columna
            context.select_font_face('monospace')
            context.set_font_size(14) # em-square height is 90 pixels
            context.move_to(10+30*a, rect.height-10) # move to point (x, y) = (10, 90)
            context.set_source_rgb(0, 0, 0)
            context.show_text(str(i))
            a += 1

        #Dibuja un zumbador
        # context.set_source_rgb(.79, 1, 0)
        # context.rectangle(origen.x, origen.y, 30, 30)
        # context.fill()

        # context.select_font_face('monospace')
        # context.set_font_size(12)
        # context.move_to(origen.x, origen.y)
        # context.set_source_rgb(0, 0, 0)
        # context.show_text('str(i+1)')

        #Pad de control
        context.set_source_rgb(.19, .35, .51) #(self.tamanio_mundo.x-70, 5, 68, 110)
        context.move_to(self.tamanio_mundo.x-70+35, 5)
        context.line_to(self.tamanio_mundo.x-70+69, 5+55)
        context.line_to(self.tamanio_mundo.x-70+35, 5+110)
        context.line_to(self.tamanio_mundo.x-70+1, 5+55)
        context.close_path()
        context.fill()

        #Controles de movimiento
        context.set_source_rgb(.38, .70, .32) #Norte
        context.move_to(rect.width-40-10, 40)
        context.line_to(rect.width-10-10, 40)
        context.line_to(rect.width-25-10, 10)
        context.close_path()
        context.fill()

        context.move_to(rect.width-40-10, 10+70) #Sur
        context.line_to(rect.width-10-10, 10+70)
        context.line_to(rect.width-25-10, 40+70)
        context.close_path()
        context.fill()

        context.move_to(rect.width-25-8, 45) #Este
        context.line_to(rect.width-25+30-8, 45+15)
        context.line_to(rect.width-25-8, 45+30)
        context.close_path()
        context.fill()

        context.move_to(rect.width-25-50+30+8, 45) #Oeste
        context.line_to(rect.width-25-50+8, 45+15)
        context.line_to(rect.width-25-50+30+8, 45+30)
        context.close_path()
        context.fill()

    def mundo_click(self, canvas, event):
        """Maneja los clicks en el mundo"""
        if (self.tamanio_mundo.x-50)<=event.x<=(self.tamanio_mundo.x-20) and 10<=event.y<=40:
            #NORTE
            if self.primera_fila+self.num_filas-2 < 100:
                self.primera_fila += 1
        elif (self.tamanio_mundo.x-50)<=event.x<=(self.tamanio_mundo.x-20) and 80<=event.y<=110:
            #SUR
            if self.primera_fila > 1:
                self.primera_fila -= 1
        elif (self.tamanio_mundo.x-50+17)<=event.x<=(self.tamanio_mundo.x-20+17) and 45<=event.y<=75:
            #ESTE
            if self.primera_columna+self.num_columnas-2 < 100:
                self.primera_columna += 1
        elif (self.tamanio_mundo.x-50+17-35)<=event.x<=(self.tamanio_mundo.x-20+17-35) and 45<=event.y<=75:
            #OESTE
            if self.primera_columna > 1:
                self.primera_columna -= 1
        else: #Pasan otras cosas
            pass
        canvas.queue_draw() #Volvemos a pintar el canvas
        #if event.x, event.y

    def gtk_main_quit(self, componente):
        Gtk.main_quit()
