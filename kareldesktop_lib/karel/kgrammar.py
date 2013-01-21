#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  kgrammar.py
#
#  Copyright 2012 Developingo <a.wonderful.code@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Sarbolt, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""
Define la gramatica de Karel
"""

__all__ = ['kgrammar']

from klexer import klexer
from kutil import KarelException
from kutil import xml_prepare
from string import ascii_letters
from collections import deque
import json
import sys

class kgrammar:
    """
    Clase que contiene y conoce la gramatica de karel
    """
    def __init__(self, flujo=sys.stdin, archivo='', strict=False, futuro=False):
        """ Inicializa la gramatica:
        flujo       indica el torrente de entrada
        archivo     es el nombre del archivo fuente, si existe
        debug       indica si es necesario imprimir mensajes para debug
        futuro      indica si se pueden usar caracteristicas del futuro
                    de Karel como las condiciones 'falso' y 'verdadero'"""
        self.strict = strict
        self.tiene_apagate = False
        self.instrucciones = ['avanza', 'gira-izquierda', 'coge-zumbador', 'deja-zumbador', 'apagate', 'sal-de-instruccion', 'sal-de-bucle', 'continua-bucle']
        #La instruccion sirve para combinarse con el bucle mientras y la condicion verdadero
        self.condiciones = [
            'frente-libre',
            'frente-bloqueado',
            'derecha-libre',
            'derecha-bloqueada',
            'izquierda-libre',
            'izquierda-bloqueada',
            'junto-a-zumbador',
            'no-junto-a-zumbador',
            'algun-zumbador-en-la-mochila',
            'ningun-zumbador-en-la-mochila',
            "orientado-al-norte",
            "no-orientado-al-norte",
            "orientado-al-este",
            "no-orientado-al-este",
            "orientado-al-sur",
            "no-orientado-al-sur",
            "orientado-al-oeste",
            "no-orientado-al-oeste",
            "si-es-cero",
            "verdadero", #Reservadas para futuros usos
            "falso" #reservadas para futuros usos
        ]
        if not futuro:
            self.condiciones = self.condiciones[:-2]
            self.instrucciones = self.instrucciones[:-2]
        self.expresiones_enteras = ['sucede', 'precede']
        self.estructuras = ['si', 'mientras', 'repite', 'repetir']
        self.palabras_reservadas = [
            "iniciar-programa",
            "inicia-ejecucion",
            "termina-ejecucion",
            "finalizar-programa",
            "no",
            "y",
            "o",
            "define-nueva-instruccion",
            "define-prototipo-instruccion",
            "inicio",
            "fin",
            "hacer",
            "veces",
            "entonces",
            "sino"
        ] + self.instrucciones + self.condiciones + self.expresiones_enteras + self.estructuras
        self.lexer = klexer(flujo, archivo)
        self.token_actual = self.lexer.get_token()
        self.prototipo_funciones = dict()
        self.funciones = dict()
        self.arbol = {
            "main": [], #Lista de instrucciones principal, declarada en 'inicia-ejecucion'
            "funciones": dict() #Diccionario con los nombres de las funciones como llave
        }
        # Un diccionario que tiene por llaves los nombres de las funciones
        # y que tiene por valores listas con las variables de dichas
        # funciones
        self.lista_programa = deque()
        self.ejecutable = {
            'lista': deque(),
            'indice_funciones': dict(),
            'main': 0
        }
        # Una lista que puede contener el árbol expandido con las instrucciones
        # del programa de forma adecuada
        self.futuro = futuro

    def avanza_token (self):
        """ Avanza un token en el archivo """
        siguiente_token = self.lexer.get_token()

        if siguiente_token:
            self.token_actual = siguiente_token
            return True
        else:
            return False

    def bloque(self):
        """
        Define un bloque en la sitaxis de karel
        {BLOQUE ::=
                [DeclaracionDeProcedimiento ";" | DeclaracionDeEnlace ";"] ...
                "INICIA-EJECUCION"
                   ExpresionGeneral [";" ExpresionGeneral]...
                "TERMINA-EJECUCION"
        }
        Un bloque se compone de todo el codigo admitido entre iniciar-programa
        y finalizar-programa
        """

        while self.token_actual == 'define-nueva-instruccion' or self.token_actual == 'define-prototipo-instruccion' or self.token_actual == 'externo':
            if self.token_actual == 'define-nueva-instruccion':
                self.declaracion_de_procedimiento()
            elif self.token_actual == 'define-prototipo-instruccion':
                self.declaracion_de_prototipo()
            else:
                #Se trata de una declaracion de enlace
                self.declaracion_de_enlace()
        #Toca verificar que todos los prototipos se hayan definido
        for funcion in self.prototipo_funciones.keys():
            if not self.funciones.has_key(funcion):
                raise KarelException("La instrucción '%s' tiene prototipo pero no fue definida"%funcion)
        #Sigue el bloque con la lógica del programa
        if self.token_actual == 'inicia-ejecucion':
            self.avanza_token()
            self.arbol['main'] = self.expresion_general([], False, False)
            if self.token_actual != 'termina-ejecucion':
                raise KarelException("Se esperaba 'termina-ejecucion' al final del bloque lógico del programa, encontré '%s'"%self.token_actual)
            else:
                self.avanza_token()

    def clausula_atomica(self, lista_variables):
        """
        Define una clausila atomica
        {
        ClausulaAtomica ::=  {
                              "SI-ES-CERO" "(" ExpresionEntera ")" |
                              FuncionBooleana |
                              "(" Termino ")"
                             }{
        }
        """
        retornar_valor = None

        if self.token_actual == 'si-es-cero':
            self.avanza_token()
            if self.token_actual == '(':
                self.avanza_token()
                retornar_valor = {'si-es-cero': self.expresion_entera(lista_variables)}
                if self.token_actual == ')':
                    self.avanza_token()
                else:
                    raise KarelException("Se esperaba ')'")
            else:
                raise KarelException("Se esperaba '('")
        elif self.token_actual == '(':
            self.avanza_token()
            retornar_valor = self.termino(lista_variables)
            if self.token_actual == ')':
                self.avanza_token()
            else:
                raise KarelException("Se esperaba ')'")
        else:
            retornar_valor = self.funcion_booleana()

        return retornar_valor

    def clausula_no(self, lista_variables):
        """
        Define una clausula de negacion
        {
            ClausulaNo ::= ["NO"] ClausulaAtomica
        }
        """
        retornar_valor = None

        if self.token_actual == 'no':
            self.avanza_token()
            retornar_valor = {'no': self.clausula_atomica(lista_variables)}
        else:
            retornar_valor = self.clausula_atomica(lista_variables)

        return retornar_valor

    def clausula_y(self, lista_variables):
        """
        Define una clausula conjuntiva
        {
            ClausulaY ::= ClausulaNo ["Y" ClausulaNo]...
        }
        """
        retornar_valor = {'y': [self.clausula_no(lista_variables)]}

        while self.token_actual == 'y':
            self.avanza_token()
            retornar_valor['y'].append(self.clausula_no(lista_variables))

        return retornar_valor

    def declaracion_de_procedimiento(self):
        """
        Define una declaracion de procedimiento
        {
            DeclaracionDeProcedimiento ::= "DEFINE-NUEVA-INSTRUCCION" Identificador ["(" Identificador ")"] "COMO"
                                         Expresion
        }
        Aqui se definen las nuevas funciones que extienden el lenguaje
        de Karel, como por ejemplo gira-derecha.
        """

        self.avanza_token()

        requiere_parametros = False #Indica si la funcion a definir tiene parametros
        nombre_funcion = ''

        if self.token_actual in self.palabras_reservadas or not self.es_identificador_valido(self.token_actual):
            raise KarelException("Se esperaba un nombre de procedimiento vÃ¡lido, '%s' no lo es"%self.token_actual)

        if self.funciones.has_key(self.token_actual):
            raise KarelException("Ya se ha definido una funcion con el nombre '%s'"%self.token_actual)
        else:
            self.funciones.update({self.token_actual: []})
            nombre_funcion = self.token_actual

        self.arbol['funciones'].update({
            nombre_funcion : {
                'params': [],
                'cola': []
            }
        })

        self.avanza_token()

        if self.token_actual == 'como':
            self.avanza_token()
        elif self.token_actual == '(':
            self.avanza_token()
            requiere_parametros = True
            while True:
                if self.token_actual in self.palabras_reservadas or not self.es_identificador_valido(self.token_actual):
                    raise KarelException("Se esperaba un nombre de variable, '%s' no es válido"%self.token_actual)
                else:
                    if self.token_actual in self.funciones[nombre_funcion]:
                        raise KarelException("La funcion '%s' ya tiene un parámetro con el nombre '%s'"%(nombre_funcion, self.token_actual))
                    else:
                        self.funciones[nombre_funcion].append(self.token_actual)
                        self.avanza_token()

                    if self.token_actual == ')':
                        self.lexer.push_token(')') #Devolvemos el token a la pila
                        break
                    elif self.token_actual == ',':
                        self.avanza_token()
                    else:
                        raise KarelException("Se esperaba ',', encontré '%s'"%self.token_actual)
            self.arbol['funciones'][nombre_funcion]['params'] = self.funciones[nombre_funcion]
        else:
            raise KarelException("Se esperaba la palabra clave 'como' o un parametro")

        if requiere_parametros:
            self.avanza_token()
            if self.token_actual != ')':
                raise KarelException("Se esperaba ')'")
            self.avanza_token()
            if self.token_actual != 'como':
                raise KarelException("se esperaba la palabra clave 'como'")
            self.avanza_token()

        if self.prototipo_funciones.has_key(nombre_funcion):
            #Hay que verificar que se defina como se planeó
            if len(self.prototipo_funciones[nombre_funcion]) != len(self.funciones[nombre_funcion]):
                raise KarelException("La función '%s' no está definida como se planeó en el prototipo, verifica el número de variables"%nombre_funcion)

        self.arbol['funciones'][nombre_funcion]['cola'] = self.expresion(self.funciones[nombre_funcion], True, False)

        if self.token_actual != ';':
            raise KarelException("Se esperaba ';'")
        else:
            self.avanza_token()

    def declaracion_de_prototipo(self):
        """
        Define una declaracion de prototipo
        {
            DeclaracionDePrototipo ::= "DEFINE-PROTOTIPO-INSTRUCCION" Identificador ["(" Identificador ")"]
        }
        Los prototipos son definiciones de funciones que se hacen previamente
        para poderse utilizar dentro de una función declarada antes.
        """

        requiere_parametros = False
        nombre_funcion = ''
        self.avanza_token()

        if self.token_actual in self.palabras_reservadas or not self.es_identificador_valido(self.token_actual):
            raise KarelException("Se esperaba un nombre de función, '%s' no es válido"%self.token_actual)
        if self.prototipo_funciones.has_key(self.token_actual):
            raise KarelException("Ya se ha definido un prototipo de funcion con el nombre '%s'"%self.token_actual)
        else:
            self.prototipo_funciones.update({self.token_actual: []})
            nombre_funcion = self.token_actual

        self.avanza_token()

        if self.token_actual == ';':
            self.avanza_token();
        elif self.token_actual == '(':
            self.avanza_token()
            requiere_parametros = True
            while True:
                if self.token_actual in self.palabras_reservadas or not self.es_identificador_valido(self.token_actual):
                    raise KarelException("Se esperaba un nombre de variable, '%s' no es válido"%self.token_actual)
                else:
                    if self.token_actual in self.prototipo_funciones[nombre_funcion]:
                        raise KarelException("El prototipo de función '%s' ya tiene un parámetro con el nombre '%s'"%(nombre_funcion, self.token_actual))
                    else:
                        self.prototipo_funciones[nombre_funcion].append(self.token_actual)
                        self.avanza_token()

                    if self.token_actual == ')':
                        self.lexer.push_token(')') #Devolvemos el token a la pila
                        break
                    elif self.token_actual == ',':
                        self.avanza_token()
                    else:
                        raise KarelException("Se esperaba ',', encontré '%s'"%self.token_actual)
        else:
            raise KarelException("Se esperaba ';' o un parámetro")

        if requiere_parametros:
            self.avanza_token()
            if self.token_actual != ')':
                raise KarelException("Se esperaba ')'")
            self.avanza_token()
            if self.token_actual != ';':
                raise KarelException("Se esperaba ';'")
            self.avanza_token()

    def declaracion_de_enlace (self):
        """ Se utilizara para tomar funciones de librerias externas,
        aun no implementado"""

    def expresion(self, lista_variables, c_funcion, c_bucle):
        """
        Define una expresion
        {
        Expresion :: = {
                          "apagate"
                          "gira-izquierda"
                          "avanza"
                          "coge-zumbador"
                          "deja-zumbador"
                          "sal-de-instruccion"
                          ExpresionLlamada
                          ExpresionSi
                          ExpresionRepite
                          ExpresionMientras
                          "inicio"
                              ExpresionGeneral [";" ExpresionGeneral] ...
                          "fin"
                       }{
        }
        Recibe para comprobar una lista con las variables válidas en
        este contexto, tambien comprueba mediante c_funcion si esta en
        un contexto donde es valido el sal-de-instruccion.
        """
        retornar_valor = []

        if self.token_actual in self.instrucciones:
            if self.token_actual == 'sal-de-instruccion':
                if c_funcion:
                    retornar_valor = [self.token_actual]
                    self.avanza_token()
                else:
                    raise KarelException("No es posible usar 'sal-de-instruccion' fuera de una instruccion :)")
            elif self.token_actual == 'sal-de-bucle' or self.token_actual == 'continua-bucle':
                if c_bucle:
                    retornar_valor = [self.token_actual]
                    self.avanza_token()
                else:
                    raise KarelException("No es posible usar '"+self.token_actual.token+"' fuera de un bucle :)")
            else:
                if self.token_actual == 'apagate':
                    self.tiene_apagate = True
                retornar_valor = [self.token_actual]
                self.avanza_token()
        elif self.token_actual == 'si':
            retornar_valor = [self.expresion_si(lista_variables, c_funcion, c_bucle)]
        elif self.token_actual == 'mientras':
            retornar_valor = [self.expresion_mientras(lista_variables, c_funcion)]
        elif self.token_actual == 'repite' or self.token_actual == 'repetir':
            retornar_valor = [self.expresion_repite(lista_variables, c_funcion)]
        elif self.token_actual == 'inicio':
            self.avanza_token()
            retornar_valor = self.expresion_general(lista_variables, c_funcion, c_bucle)
            if self.token_actual == 'fin':
                self.avanza_token()
            else:
                raise KarelException("Se esperaba 'fin' para concluir el bloque, encontré '%s'"%self.token_actual)
        elif self.token_actual not in self.palabras_reservadas and self.es_identificador_valido(self.token_actual):
            #Se trata de una instrucción creada por el usuario
            if self.prototipo_funciones.has_key(self.token_actual) or self.funciones.has_key(self.token_actual):
                nombre_funcion = self.token_actual
                retornar_valor = [{
                    'estructura': 'instruccion',
                    'nombre': nombre_funcion,
                    'argumento': []
                }]
                self.avanza_token()
                requiere_parametros = True
                num_parametros = 0
                if self.token_actual == '(':
                    self.avanza_token()
                    while True:
                        retornar_valor[0]['argumento'].append(self.expresion_entera(lista_variables))
                        num_parametros += 1
                        if self.token_actual == ')':
                            #self.lexer.push_token(')') #Devolvemos el token a la pila
                            break
                        elif self.token_actual == ',':
                            self.avanza_token()
                        else:
                            raise KarelException("Se esperaba ',', encontré '%s'"%self.token_actual)
                    if not self.futuro and num_parametros>1:
                        raise KarelException("No están habilitadas las funciones con varios parámetros")
                    self.avanza_token()
                if self.prototipo_funciones.has_key(nombre_funcion):
                    if num_parametros != len(self.prototipo_funciones[nombre_funcion]):
                        raise KarelException("Estas intentando llamar la funcion '%s' con %d parámetros, pero así no fue definida"%(nombre_funcion, num_parametros))
                else:
                    if num_parametros != len(self.funciones[nombre_funcion]):
                        raise KarelException("Estas intentando llamar la funcion '%s' con %d parámetros, pero así no fue definida"%(nombre_funcion, num_parametros))
            else:
                raise KarelException("La instrucción '%s' no ha sido previamente definida, pero es utilizada"%self.token_actual)
        else:
            raise KarelException("Se esperaba un procedimiento, '%s' no es válido"%self.token_actual)

        return retornar_valor

    def expresion_entera(self, lista_variables):
        """
        Define una expresion numerica entera
        {
            ExpresionEntera ::= { Decimal | Identificador | "PRECEDE" "(" ExpresionEntera ")" | "SUCEDE" "(" ExpresionEntera ")" }{
        }
        """
        retornar_valor = None
        #En este punto hay que verificar que se trate de un numero entero
        es_numero = False
        if self.es_numero(self.token_actual):
            #Intentamos convertir el numero
            retornar_valor = int(self.token_actual)
            es_numero = True
        else:
            #No era un entero
            if self.token_actual in self.expresiones_enteras:
                retornar_valor = {
                    self.token_actual: None
                }
                self.avanza_token()
                if self.token_actual == '(':
                    self.avanza_token()
                    retornar_valor[retornar_valor.keys()[0]] = self.expresion_entera(lista_variables)
                    if self.token_actual == ')':
                        self.avanza_token()
                    else:
                        raise KarelException("Se esperaba ')'")
                else:
                    raise KarelException("Se esperaba '('")
            elif self.token_actual not in self.palabras_reservadas and self.es_identificador_valido(self.token_actual):
                #Se trata de una variable definida por el usuario
                if self.token_actual not in lista_variables:
                    raise KarelException("La variable '%s' no está definida en este contexto"%self.token_actual)
                retornar_valor = self.token_actual
                self.avanza_token()
            else:
                raise KarelException("Se esperaba un entero, variable, sucede o predece, '%s' no es válido"%self.token_actual)
        if es_numero:
            #Si se pudo convertir, avanzamos
            self.avanza_token()

        return retornar_valor

    def expresion_general(self, lista_variables, c_funcion, c_bucle):
        """
        Define una expresion general
        { Expresion | ExpresionVacia }
        Generalmente se trata de una expresión dentro de las etiquetas
        'inicio' y 'fin' o entre 'inicia-ejecucion' y 'termina-ejecucion'
        """
        retornar_valor = [] #Una lista de funciones

        while self.token_actual != 'fin' and self.token_actual != 'termina-ejecucion':
            retornar_valor += self.expresion(lista_variables, c_funcion, c_bucle)
            if self.token_actual != ';' and self.token_actual != 'fin' and self.token_actual != 'termina-ejecucion':
                raise KarelException("Se esperaba ';'")
            elif self.token_actual == ';':
                self.avanza_token()
            elif self.token_actual == 'fin':
                raise KarelException("Se esperaba ';'")
            elif self.token_actual == 'termina-ejecucion':
                raise KarelException("Se esperaba ';'")

        return retornar_valor

    def expresion_mientras(self, lista_variables, c_funcion):
        """
        Define la expresion del bucle MIENTRAS
        {
        ExpresionMientras ::= "Mientras" Termino "hacer"
                                  Expresion
        }
        """
        retornar_valor = {
            'estructura': 'mientras',
            'argumento': None,
            'cola': []
        }
        self.avanza_token()

        retornar_valor['argumento'] = self.termino(lista_variables)

        if self.token_actual != 'hacer':
            raise KarelException("Se esperaba 'hacer'")
        self.avanza_token()
        retornar_valor['cola'] = self.expresion(lista_variables, c_funcion, True)

        return retornar_valor

    def expresion_repite(self, lista_variables, c_funcion):
        """
        Define la expresion del bucle REPITE
        {
        ExpresionRepite::= "repetir" ExpresionEntera "veces"
                              Expresion
        }
        """
        retornar_valor = {
            'estructura': 'repite',
            'argumento': None,
            'cola': []
        }

        self.avanza_token()
        retornar_valor['argumento'] = self.expresion_entera(lista_variables)

        if self.token_actual != 'veces':
            raise KarelException("Se esperaba la palabra 'veces', '%s' no es válido"%self.token_actual)

        self.avanza_token()
        retornar_valor['cola'] = self.expresion(lista_variables, c_funcion, True)

        return retornar_valor

    def expresion_si(self, lista_variables, c_funcion, c_bucle):
        """
        Define la expresion del condicional SI
        {
        ExpresionSi ::= "SI" Termino "ENTONCES"
                             Expresion
                        ["SINO"
                               Expresion
                        ]
        }
        """
        retornar_valor = {
            'estructura': 'si',
            'argumento': None,
            'cola': []
        }

        self.avanza_token()

        retornar_valor['argumento'] = self.termino(lista_variables)

        if self.token_actual != 'entonces':
            raise KarelException("Se esperaba 'entonces'")

        self.avanza_token()

        retornar_valor['cola'] = self.expresion(lista_variables, c_funcion, c_bucle)

        if self.token_actual == 'sino':
            retornar_valor.update({'sino-cola': []})
            self.avanza_token()
            retornar_valor['sino-cola'] = self.expresion(lista_variables, c_funcion, c_bucle)

        return retornar_valor

    def funcion_booleana(self):
        """
        Define una funcion booleana del mundo de karel
        {
        FuncionBooleana ::= {
                               "FRENTE-LIBRE"
                               "FRENTE-BLOQUEADO"
                               "DERECHA-LIBRE"
                               "DERECHA-BLOQUEADA"
                               "IZQUIERAD-LIBRE"
                               "IZQUIERDA-BLOQUEADA"
                               "JUNTO-A-ZUMBADOR"
                               "NO-JUNTO-A-ZUMBADOR"
                               "ALGUN-ZUMBADOR-EN-LA-MOCHILA"
                               "NINGUN-ZUMBADOR-EN-LA-MOCHILA"
                               "ORIENTADO-AL-NORTE"
                               "NO-ORIENTADO-AL-NORTE"
                               "ORIENTADO-AL-ESTE"
                               "NO-ORIENTADO-AL-ESTE"
                               "ORIENTADO-AL-SUR"
                               "NO-ORIENTADO-AL-SUR"
                               "ORIENTADO-AL-OESTE"
                               "NO-ORIENTADO-AL-OESTE"
                               "VERDADERO"
                               "FALSO"
                            }{
        }
        Son las posibles funciones booleanas para Karel
        """
        retornar_valor = ""

        if self.token_actual in self.condiciones:
            retornar_valor = self.token_actual
            self.avanza_token()
        else:
            raise KarelException("Se esperaba una condición como 'frente-libre', '%s' no es una condición"%self.token_actual)

        return retornar_valor

    def termino(self, lista_variables):
        """
        Define un termino
        {
            Termino ::= ClausulaY [ "o" ClausulaY] ...
        }
        Se usan dentro de los condicionales 'si' y el bucle 'mientras'
        """
        retornar_valor = {'o': [self.clausula_y(lista_variables)]} #Lista con las expresiones 'o'

        while self.token_actual == 'o':
            self.avanza_token()
            retornar_valor['o'].append(self.clausula_y(lista_variables))

        return retornar_valor

    def verificar_sintaxis (self):
        """ Verifica que este correcta la gramatica de un programa
        en karel """
        if self.token_actual == 'iniciar-programa':
            if self.avanza_token():
                self.bloque()
                if self.token_actual != 'finalizar-programa':
                    raise KarelException("Se esperaba 'finalizar-programa' al final del codigo")
            else:
                raise KarelException("Codigo mal formado")
        else:
            raise KarelException("Se esperaba 'iniciar-programa' al inicio del programa")
        if self.strict and (not self.tiene_apagate):
            raise KarelException("Tu código no tiene 'apagate', esto no es permitido en el modo estricto")

    def es_identificador_valido(self, token):
        """ Identifica cuando una cadena es un identificador valido,
        osea que puede ser usado en el nombre de una variable, las
        reglas son:
        * Debe comenzar en una letra
        * Sólo puede tener letras, números, '-' y '_' """
        es_valido = True
        i = 0
        for caracter in token:
            if i == 0:
                if caracter not in ascii_letters:
                    #Un identificador válido comienza con una letra
                    es_valido = False
                    break
            else:
                if caracter not in self.lexer.palabras+self.lexer.numeros:
                    es_valido = False
                    break
            i += 1
        return es_valido

    def es_numero(self, token):
        """Determina si un token es un numero"""
        for caracter in token:
            if caracter not in self.lexer.numeros:
                return False #Encontramos algo que no es numero
        return True

    def guardar_compilado (self, nombrearchivo, expandir=False):
        """ Guarda el resultado de una compilacion de codigo Karel a el
        archivo especificado """
        f = file(nombrearchivo, 'w')
        if expandir:
            f.write(json.dumps(self.arbol, indent=2))
        else:
            f.write(json.dumps(self.arbol))
        f.close()

    def expandir_arbol(self):
        """Expande el árbol de instrucciones para ser usado por krunner
        durante la ejecución"""
        for funcion in self.arbol['funciones']:#Itera sobre llaves
            nueva_funcion = {
                funcion: {
                    'params': self.arbol['funciones'][funcion]['params']
                }
            }
            self.lista_programa.append(nueva_funcion)
            posicion_inicio = len(self.lista_programa)-1

            self.ejecutable['indice_funciones'].update({
                funcion: posicion_inicio
            })
            self.expandir_arbol_recursivo(self.arbol['funciones'][funcion]['cola'])
            self.lista_programa.append({
                'fin': {
                    'estructura': 'instruccion',
                    'nombre': funcion,
                    'inicio': posicion_inicio
                }
            })
        self.ejecutable['main'] = len(self.lista_programa)
        self.expandir_arbol_recursivo(self.arbol['main'])
        self.lista_programa.append('fin') #Marca de fin del programa
        self.ejecutable['lista'] = self.lista_programa
        return self.ejecutable

    def expandir_arbol_recursivo(self, cola):
        """Toma un arbol y lo expande"""
        for elem in cola: #Expande cada uno de los elementos de una cola
            if elem in self.instrucciones:
                self.lista_programa.append(elem)
            else:#Se trata de un diccionario
                if elem['estructura'] in ['repite', 'mientras']:
                    posicion_inicio = len(self.lista_programa)
                    nueva_estructura = {
                        elem['estructura']: {
                            'argumento': elem['argumento'],
                            'id': posicion_inicio
                        }
                    }

                    self.lista_programa.append(nueva_estructura)
                    self.expandir_arbol_recursivo(elem['cola'])
                    posicion_fin = len(self.lista_programa)
                    self.lista_programa.append({
                        'fin': {
                            'estructura': elem['estructura'],
                            'inicio': posicion_inicio
                        }
                    })
                    self.lista_programa[posicion_inicio][elem['estructura']].update({'fin': posicion_fin})
                elif elem['estructura'] == 'si':
                    posicion_inicio = len(self.lista_programa)
                    nueva_estructura = {
                        elem['estructura']: {
                            'argumento': elem['argumento'],
                            'id' : posicion_inicio
                        }
                    }

                    self.lista_programa.append(nueva_estructura)
                    self.expandir_arbol_recursivo(elem['cola'])
                    posicion_fin = len(self.lista_programa)
                    self.lista_programa.append({
                        'fin': {
                            'estructura': elem['estructura'],
                            'inicio': posicion_inicio,
                            'fin':posicion_fin+1
                        }
                    })
                    self.lista_programa[posicion_inicio]['si'].update({'fin': posicion_fin})
                    if elem.has_key('sino-cola'):
                        nueva_estructura = {
                            'sino': {}
                        }
                        self.lista_programa.append(nueva_estructura)
                        self.expandir_arbol_recursivo(elem['sino-cola'])
                        fin_sino = len(self.lista_programa)
                        self.lista_programa.append({
                            'fin': {
                                'estructura': 'sino'
                            }
                        })
                        self.lista_programa[posicion_fin]['fin']['fin'] = fin_sino
                else:#Se trata de la llamada a una función
                    nueva_estructura = {
                        elem['estructura']: {
                            'argumento': elem['argumento'],
                            'nombre': elem['nombre']
                        }
                    }
                    self.lista_programa.append(nueva_estructura)

if __name__ == "__main__":
    #Cosas para pruebas
    #Se usa con:
    #$ python kgrammar.py archivo.karel
    from pprint import pprint
    from time import time
    inicio = time()
    deb = False
    if deb:
        print "<xml>" #Mi grandiosa idea del registro XML, Ajua!!
    if len(sys.argv) == 1:
        grammar = kgrammar(debug=deb, futuro=True)
    else:
        fil = sys.argv[1]
        grammar = kgrammar(flujo=open(fil), archivo=fil, debug=deb, futuro=True)
    try:
        grammar.verificar_sintaxis()
        #grammar.guardar_compilado('codigo.kcmp', True)
    except KarelException, ke:
        print ke.args[0], "en la línea", grammar.lexer.linea, "columna", grammar.lexer.columna
        print
        print "<syntax status='bad'/>"
    else:
        print "Sintaxis correcta"
        print "----------"
    finally:
        pprint(grammar.arbol)
        grammar.expandir_arbol()
        print "----------"
        for i in xrange(len(grammar.lista_programa)):
            print i,grammar.lista_programa[i]
        print "----------"
    if deb:
        print "</xml>"
    fin = time()
    print "time: ", fin-inicio
