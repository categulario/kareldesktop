# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext, math
from gettext import gettext as _
gettext.textdomain('kareldesktop')

from gi.repository import Gtk # pylint: disable=E0611
from collections import deque
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

        self.primera_fila = 1
        self.primera_columna = 1

        self.borrar_zumbadores = False

        #Cosas del menejo de archivos
        self.nombre_archivo_mundo = ''
        self.mundo_guardado = True

        self.nombre_archivo_codigo = ''
        self.codigo_guardado = True

        #Un componente de la interfaz para los dialogos
        self.RESPUESTA_SI = 'si'
        self.RESPUESTA_NO = 'no'
        self.RESPUESTA_CANCELAR = 'cancelar'
        self.respuesta = self.RESPUESTA_SI #Puede ser 'no' o 'cancelar'

        self.pila_funciones = deque() # Se encarga de gestionar las funciones ligadas

        # Manejadores del canvas del mundo

    def dibuja_mundo(self, dwarea, context):
        rect = dwarea.get_allocation()

        self.mundo_ancho = rect.width
        self.mundo_alto = rect.height

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

        #Dibujar las cosas que pertenecen al mundo por cada casilla
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

                #Paredes
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

                #Zumbadores
                if casilla['zumbadores'] == -1 or casilla['zumbadores']>0:
                    if casilla['zumbadores'] == -1:
                        context.set_source_rgb(0, 1, 0)
                        context.rectangle(origen.x+(num_columna-1)*30+8, origen.y-(num_fila-1)*30+8, 16, 12)
                        context.fill()

                        context.select_font_face('monospace')
                        context.set_font_size(25)
                        context.move_to(origen.x+(num_columna-1)*30+9, origen.y-(num_fila-1)*30+23)
                        context.set_source_rgb(0, 0, 0)
                        context.show_text('∞')
                    elif casilla['zumbadores'] < 10:
                        context.set_source_rgb(0, 1, 0)
                        context.rectangle(origen.x+(num_columna-1)*30+9, origen.y-(num_fila-1)*30+8, 12, 14)
                        context.fill()

                        context.select_font_face('monospace')
                        context.set_font_size(12)
                        context.move_to(origen.x+(num_columna-1)*30+11, origen.y-(num_fila-1)*30+20)
                        context.set_source_rgb(0, 0, 0)
                        context.show_text(str(casilla['zumbadores']))
                    else:
                        context.set_source_rgb(0, 1, 0)
                        context.rectangle(origen.x+(num_columna-1)*30+7, origen.y-(num_fila-1)*30+8, 16, 14)
                        context.fill()

                        context.select_font_face('monospace')
                        context.set_font_size(12)
                        context.move_to(origen.x+(num_columna-1)*30+8, origen.y-(num_fila-1)*30+20)
                        context.set_source_rgb(0, 0, 0)
                        context.show_text(str(casilla['zumbadores']))

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

        #Actualizamos el indicador de zumbadores
        if self.mundo.obten_mochila() == -1:
            self.builder.get_object('inf_beeperbag_toggle').set_active(True)
        else:
            self.builder.get_object('mochila_entry').set_text(str(self.mundo.obten_mochila()))
        self.pon_titulo()

    def pon_titulo(self):
        self.set_title(['* - ', ''][self.codigo_guardado]+' %s [Karel] %s '%(self.nombre_archivo_codigo.split('/')[-1], self.nombre_archivo_mundo.split('/')[-1])+['*', ''][self.mundo_guardado])

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
            columna = int(event.x/30) + self.primera_columna-1
            fila = int((self.mundo_alto-event.y)/30) + self.primera_fila-1

            excedente_horizontal = event.x/30 - int(event.x/30)
            excedente_vertical = (self.mundo_alto-event.y)/30 - int((self.mundo_alto-event.y)/30)

            if 0<fila<101 and 0<columna<101:
                if event.button == 1:
                    if .25<excedente_horizontal<.75 and .25<excedente_vertical<.75:
                        if self.borrar_zumbadores:
                            self.mundo.pon_zumbadores((fila, columna), 0)
                        else:
                            zumbadores = self.mundo.obten_zumbadores((fila, columna))
                            if zumbadores >= 0:
                                self.mundo.pon_zumbadores((fila, columna), zumbadores+1)
                    elif excedente_horizontal > excedente_vertical:
                        if excedente_horizontal > 1 - excedente_vertical:
                            self.mundo.conmuta_pared((fila, columna), 'este')
                        else:
                            self.mundo.conmuta_pared((fila, columna), 'sur')
                    else:
                        if excedente_horizontal > 1 - excedente_vertical:
                            self.mundo.conmuta_pared((fila, columna), 'norte')
                        else:
                            self.mundo.conmuta_pared((fila, columna), 'oeste')
                    self.mundo_guardado = False
                elif event.button == 2:
                    print 'boton medio'
                elif event.button == 3:
                    self.coordenadas = (fila, columna)
                    self.builder.get_object('mundo_canvas_context_menu').popup(None, None, None, None, 3, event.time)
        canvas.queue_draw() #Volvemos a pintar el canvas

    def mundo_canvas_scroll_event(self, canvas, event):
        if event.delta_y < 0:
            if self.primera_fila+self.num_filas-2 < 100:
                self.primera_fila += 1
        if event.delta_y > 0:
            if self.primera_fila > 1:
                self.primera_fila -= 1
        if event.delta_x > 0:
            if self.primera_columna+self.num_columnas-2 < 100:
                self.primera_columna += 1
        if event.delta_x < 0:
            if self.primera_columna > 1:
                self.primera_columna -= 1
        canvas.queue_draw()

        # Componentes de la interfaz relativos al mundo

    def inf_beeperbag_toggle_toggled(self, event):
        if event.get_active(): #Activa zumbadores infinitos
            self.builder.get_object('mochila_entry').set_editable(False)
            self.mundo.establece_mochila('inf')
        else: #Zumbadores en númeroo
            self.builder.get_object('mochila_entry').set_editable(True)
            self.mundo.establece_mochila(int(self.builder.get_object('mochila_entry').get_text()))
        self.mundo_guardado = False
        self.builder.get_object('mundo_canvas').queue_draw()

    def karel_al_este_activate(self, event):
        self.mundo.establece_karel(self.coordenadas, 'este')
        self.mundo_guardado = False
        event.queue_draw()

    def karel_al_norte_activate(self, event):
        self.mundo.establece_karel(self.coordenadas, 'norte')
        self.mundo_guardado = False
        event.queue_draw()

    def karel_al_sur_activate(self, event):
        self.mundo.establece_karel(self.coordenadas, 'sur')
        self.mundo_guardado = False
        event.queue_draw()

    def karel_al_oeste_activate(self, event):
        self.mundo.establece_karel(self.coordenadas, 'oeste')
        self.mundo_guardado = False
        event.queue_draw()

    def n_zumbadores_item_activate(self, event):
        self.builder.get_object('n_zumbadores_dialog').show_all()

    def inf_zumbadores_item_activate(self, event):
        self.mundo.pon_zumbadores(self.coordenadas, 'inf')
        self.mundo_guardado = False
        event.queue_draw()

    def zero_zumbadores_item_activate(self, event):
        self.mundo.pon_zumbadores(self.coordenadas, 0)
        self.mundo_guardado = False
        event.queue_draw()

    def n_zumbadores_aceptar_btn_clicked(self, event):
        n_zumbadores = event.get_text()
        try:
            zumbadores = int(n_zumbadores)
            if zumbadores == -1:
                self.mundo.pon_zumbadores(self.coordenadas, 'inf')
            elif zumbadores >= 0:
                self.mundo.pon_zumbadores(self.coordenadas, zumbadores)
        except ValueError:
            if n_zumbadores == 'inf' or n_zumbadores == 'infinito' or n_zumbadores == 'infinity':
                self.mundo.pon_zumbadores(self.coordenadas, 'inf')

        self.builder.get_object('n_zumbadores_dialog').hide()
        self.mundo_guardado = False
        self.builder.get_object('mundo_canvas').queue_draw()

    def n_zumbadores_entry_key_release_event_cb(self, entry, event):
        if event.keyval == 65293:
            n_zumbadores = entry.get_text()
            try:
                zumbadores = int(n_zumbadores)
                if zumbadores == -1:
                    self.mundo.pon_zumbadores(self.coordenadas, 'inf')
                elif zumbadores >= 0:
                    self.mundo.pon_zumbadores(self.coordenadas, zumbadores)
            except ValueError:
                if n_zumbadores == 'inf' or n_zumbadores == 'infinito' or n_zumbadores == 'infinity':
                    self.mundo.pon_zumbadores(self.coordenadas, 'inf')

            self.builder.get_object('n_zumbadores_dialog').hide()
            self.mundo_guardado = False
            self.builder.get_object('mundo_canvas').queue_draw()

    def n_zumbadores_cancelar_btn_clicked(self, event):
        self.builder.get_object('n_zumbadores_dialog').hide()

    def btn_borrar_zumbador_toggled(self, event):
        self.borrar_zumbadores = event.get_active()

        #Otros componentes de la interfaz

    def go_home(self, event):
        self.primera_fila = 1
        self.primera_columna = 1
        event.queue_draw()

    def mundo_regresar(self, event):
        self.show_confirm(
            'Esto borrará toda la información del mundo actual ¿Continuamos?',
            self.mundo_regresar_hacer,
            None
        )

    def mundo_regresar_hacer(self):
        self.mundo = kworld(karel_pos=(1,1), orientacion='norte', mochila=0, casillas=dict())
        self.mundo_guardado = False
        self.builder.get_object('mundo_canvas').queue_draw()

    def mundo_nuevo(self, event=None):
        if not self.mundo_guardado:
            self.show_confirm(
                '¿Quieres guardar el mundo anterior antes de crear un mundo nuevo?',
                self.mundo_guardar,
                self.mundo_nuevo_hacer
            )
        else:
            self.mundo_nuevo_hacer()

    def mundo_nuevo_hacer(self):
        self.mundo = kworld(karel_pos=(1,1), orientacion='norte', mochila=0, casillas=dict())
        self.mundo_guardado = True
        self.nombre_archivo_mundo = ''
        self.builder.get_object('mundo_canvas').queue_draw()

    def mundo_abrir(self, event):
        if not self.mundo_guardado:
            self.show_confirm(
                '¿Quieres guardar el mundo anterior antes de abrir uno nuevo?',
                self.mundo_guardar,
                event.show_all
            )
        else:
            event.show_all()

    def mundo_abrir_cancelar(self, event):
        event.hide()

    def mundo_abrir_aceptar(self, event):
        archivo = event.get_filename()

        if archivo is not None: #Tiene una ruta válida
            try:
                f = file(archivo)
            except IOError:
                self.show_dialog('No se puede leer este archivo')
            else:
                if self.mundo.carga_archivo(f):
                    self.nombre_archivo_mundo = archivo
                    self.mundo_guardado = True
                    self.builder.get_object('mundo_canvas').queue_draw()
                    #Ahora gestiona los zumbadores en la mochila
                    if self.mundo.obten_mochila() == -1:
                        self.builder.get_object('inf_beeperbag_toggle').set_active(True)
                    else:
                        self.builder.get_object('mochila_entry').set_text(str(self.mundo.obten_mochila()))
                else:
                    self.show_dialog('No es un archivo de mundo válido')

        event.hide()

    def mundo_guardar(self, event=None):
        if self.nombre_archivo_mundo != '':
            try:
                self.mundo.exporta_mundo(self.nombre_archivo_mundo)
            except IOError, e:
                print e
                self.show_dialog('No se pudo escribir el archivo')
            else:
                self.mundo_guardado = True
                self.pon_titulo()
            #Procesamos la cola de funciones si existe
            if len(self.pila_funciones) > 0:
                funcion = self.pila_funciones.pop()
                funcion()
        else:
            self.builder.get_object('world_save_dialog').show_all()

    def mundo_guardar_como(self, event=None):
        self.builder.get_object('world_save_dialog').show_all()

    def mundo_guardar_aceptar(self, event):
        archivo = event.get_filename()

        if archivo is not None: #Tiene una ruta válida
            try:
                if not archivo.endswith('.world'):
                    archivo += '.world'
                self.mundo.exporta_mundo(archivo)
            except IOError:
                self.show_dialog('No se puede escribir en este archivo')
            else:
                self.mundo_guardado = True
                self.nombre_archivo_mundo = archivo
                self.pon_titulo()
        event.hide()
        #Procesamos la cola de funciones si existe
        if len(self.pila_funciones) > 0:
            funcion = self.pila_funciones.pop()
            funcion()

    def mundo_guardar_cancelar(self, event):
        event.hide()

    def mochila_entry_changed(self, event):
        texto = event.get_text()
        try:
            mochila = int(texto)
            self.mundo.establece_mochila(mochila)
            self.mundo_guardado = False
        except ValueError:
            if texto != '':
                event.set_text('0')
        self.pon_titulo()

        #Dialogo general y de confirmacion

    def show_dialog(self, message):
        self.builder.get_object('general_dialog_label').set_text(message)
        self.builder.get_object('general_dialog').show_all()

    def general_dialog_aceptar_clicked(self, event):
        event.hide()

    def show_confirm(self, message, funcion_si, funcion_final):
        """Muestra un diálogo de confirmacion y apunta la funcion
        indicada para ejecutarse en caso afirmativo"""
        self.builder.get_object('confirm_dialog_label').set_text(message)
        self.builder.get_object('confirm_dialog').show_all()

        if funcion_final:
            self.pila_funciones.append(funcion_final)
        self.pila_funciones.append(funcion_si)

    def confirm_dialog_cancelar_clicked(self, event):
        event.hide()

    def confirm_dialog_no_clicked(self, event):
        if len(self.pila_funciones) > 0:
            self.pila_funciones.pop() #botamos la última función de la pila que correspondía al si
        event.hide()
        if len(self.pila_funciones) > 0:
            funcion = self.pila_funciones.pop()
            funcion()

    def confirm_dialog_si_clicked(self, event):
        funcion = self.pila_funciones.pop()
        event.hide()
        funcion()

        #Bucle principal

    def gtk_main_quit(self, componente):
        if not self.mundo_guardado:
            self.show_confirm('¿Desea salvar este mundo antes de partir?', self.mundo_guardar, Gtk.main_quit)
        else:
            Gtk.main_quit()

    def kareldesktop_window_destroy(self, a, b):
        if not self.mundo_guardado:
            self.show_confirm('¿Desea salvar este mundo antes de partir?', self.mundo_guardar, Gtk.main_quit)
