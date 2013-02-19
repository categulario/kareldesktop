# -*- coding: utf-8 -*-
"""
Clases y funciones utiles para Karel
"""

from collections import deque

__all__ = ['KarelException', 'xml_prepare']

class ktoken(object):
    """Define un token de la gramática de karel. Esencialmente un token
    es un trozo de cadena, sin embargo para esta gramática podría ser un"""
    #TODO implementar la posición del token
    POSICION_INICIO = 'ini'
    POSICION_FIN = 'fin'
    POSICION_MEDIO = 'med'
    def __init__(self, s_token, linea, columna, posicion):
        """Inicializa el token con un token cadena"""
        self.token = s_token
        self.linea = linea
        self.columna = columna
        self.posicion = posicion

    def lower(self):
        self.token = self.token.lower()

    def startswith(self, cad):
        return self.token.startswith(cad)

    def __str__(self):
        return self.token

    def __repr__(self):
        return repr(self.token)

    def __int__(self):
        return int(self.token)

    def __eq__(self, cad):
        return self.token == cad

    def __ne__(self, cad):
        return self.token != cad

    def __iter__(self):
        return (i for i in self.token)

    def __hash__(self):
        return hash(self.token)

    def __getitem__(self, index):
        return self.token.__getitem__(index)

class kstack(deque):
    """Una pila eficiente para karel el robot"""
    def top(self):
        """Devuelve el tope de la pila"""
        return self[-1]

    def is_empty(self):
        """indica cuando la pila está vacía"""
        return len(self)==0

    def en_tope(self, id):
        """indica si el id indicado está en el tope de la pila"""
        if self.is_empty():
            return False
        for i in self.top():#itera sobre la única llave
            return self.top()[i]['id'] == id

class KarelException(Exception):
    """ Define un error sintactico de Karel """
    pass

def xml_prepare(lista):
    """ prepara una lista para ser mostrada por sus parametros en un
    atributo de etiqueta XML"""
    s = ""
    for i in lista:
        s += str(i)+" "
    return s[:-1]

if __name__ == '__main__':
    print ktoken('(') == '('
