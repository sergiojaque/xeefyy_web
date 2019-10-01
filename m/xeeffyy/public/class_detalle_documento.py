#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_cuenta import cms_cuenta as class_cuenta
from orm.common_services.public.cms_documento import cms_documento as class_documento
from orm.common_services.public.cms_unidad import cms_unidad as class_unidad
from orm.common_services.public.cms_contexto import cms_contexto as class_contexto
from lib_dev.pyBernateImp import *


class class_detalle_documento(pyBernateImp):
    table = 'detalle_documento'
    schema = 'public'
    comment = 'detalle documento'

    def __init__(self, cnx=None):
        pyBernateImp.__init__(self, cnx)
        self._exists = False
        self._cod_detalle_documento = None
        self._desc_detalle_documento = None
        self._user_id = None
        self._cuenta = class_cuenta(cnx)
        self._documento = class_documento(cnx)
        self._unidad = class_unidad(cnx)
        self._decimales = None
        self._valor = None
        self._contexto = class_contexto(cnx)
        self.map = {}
        self.map['cod_detalle_documento'] = (
            1, 'p', int, int(), True, True, 64, False, 'cod_detalle_documento', 'pkdetalle_documento')
        self.map['desc_detalle_documento'] = (2, 'None', str, str(), True, False, None, True, 'Observacion', 'None')
        self.map['user_id'] = (5, 'None', str, str(), False, False, 50, True, 'user_id', 'None')
        self.map['cod_cuenta'] = (6, 'None', int, int(), False, False, 64, True, 'cod_cuenta', 'None')
        self.map['cod_documento'] = (7, 'None', int, int(), False, False, 64, True, 'cod_documento', 'None')
        self.map['cod_unidad'] = (8, 'None', int, int(), False, False, 64, True, 'cod_unidad', 'None')
        self.map['decimales'] = (9, 'None', int, int(), False, False, 32, True, 'decimales', 'None')
        self.map['valor'] = (10, 'None', int, int(), False, False, 64, True, 'valor', 'None')
        self.map['cod_contexto'] = (11, 'None', int, int(), False, False, 64, True, 'cod_contexto', 'None')
        self.one2many = {}
        self._gen_pk = "select nextval('public.detalle_documento_cod_detalle_documento_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'detalle_documento'

    def get(self):

        r = self.select_criterial(self, limit=1)
        if len(r) != 0:
            return r[0]
        else:
            return self

    def save(self):

        try:
            response = self._validate(self)
            if not response == True:
                print response
                return
            if self._exists:
                self._update(self)
            else:
                self._save(self)

        except:
            raise sys.exc_info()[1]

    def delete(self):

        try:
            self._delete(self)
        except:
            self.rollback()
            raise sys.exc_info()[1]

    def get_cod_detalle_documento(self):
        return self._cod_detalle_documento

    def set_cod_detalle_documento(self, valor):
        self._cod_detalle_documento = int(valor)

    cod_detalle_documento = property(fget=get_cod_detalle_documento, fset=set_cod_detalle_documento)

    def get_desc_detalle_documento(self):
        return self._desc_detalle_documento

    def set_desc_detalle_documento(self, valor):
        self._desc_detalle_documento = str(valor)

    desc_detalle_documento = property(fget=get_desc_detalle_documento, fset=set_desc_detalle_documento)

    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id = str(valor)

    user_id = property(fget=get_user_id, fset=set_user_id)

    def get_cuenta(self):
        if self._cuenta == self:
            self._cuenta = self.__class__(self.cnx)
        if self._cuenta._exists:
            return self._cuenta
        else:
            r = self._cuenta.get()
            self._cuenta = r
            return r

    def set_cuenta(self, valor):
        self._cuenta = valor

    cuenta = property(fget=get_cuenta, fset=set_cuenta)

    def get_cod_cuenta(self):
        if self._cuenta == self:
            self._cuenta = self.__class__(self.cnx)
        return self._cuenta.get_cod_cuenta()

    def set_cod_cuenta(self, valor):
        self._cuenta = self._cuenta.__class__(self.cnx)
        self._cuenta.set_cod_cuenta(int(valor))

    cod_cuenta = property(fget=get_cod_cuenta, fset=set_cod_cuenta)

    def get_documento(self):
        if self._documento == self:
            self._documento = self.__class__(self.cnx)
        if self._documento._exists:
            return self._documento
        else:
            r = self._documento.get()
            self._documento = r
            return r

    def set_documento(self, valor):
        self._documento = valor

    documento = property(fget=get_documento, fset=set_documento)

    def get_cod_documento(self):
        if self._documento == self:
            self._documento = self.__class__(self.cnx)
        return self._documento.get_cod_documento()

    def set_cod_documento(self, valor):
        self._documento = self._documento.__class__(self.cnx)
        self._documento.set_cod_documento(int(valor))

    cod_documento = property(fget=get_cod_documento, fset=set_cod_documento)

    def get_unidad(self):
        if self._unidad == self:
            self._unidad = self.__class__(self.cnx)
        if self._unidad._exists:
            return self._unidad
        else:
            r = self._unidad.get()
            self._unidad = r
            return r

    def set_unidad(self, valor):
        self._unidad = valor

    unidad = property(fget=get_unidad, fset=set_unidad)

    def get_cod_unidad(self):
        if self._unidad == self:
            self._unidad = self.__class__(self.cnx)
        return self._unidad.get_cod_unidad()

    def set_cod_unidad(self, valor):
        self._unidad = self._unidad.__class__(self.cnx)
        self._unidad.set_cod_unidad(int(valor))

    cod_unidad = property(fget=get_cod_unidad, fset=set_cod_unidad)

    def get_decimales(self):
        return self._decimales

    def set_decimales(self, valor):
        self._decimales = int(valor)

    decimales = property(fget=get_decimales, fset=set_decimales)

    def get_valor(self):
        return self._valor

    def set_valor(self, valor):
        self._valor = int(valor)

    valor = property(fget=get_valor, fset=set_valor)

    def get_contexto(self):
        if self._contexto == self:
            self._contexto = self.__class__(self.cnx)
        if self._contexto._exists:
            return self._contexto
        else:
            r = self._contexto.get()
            self._contexto = r
            return r

    def set_contexto(self, valor):
        self._contexto = valor

    contexto = property(fget=get_contexto, fset=set_contexto)

    def get_cod_contexto(self):
        if self._contexto == self:
            self._contexto = self.__class__(self.cnx)
        return self._contexto.get_cod_contexto()

    def set_cod_contexto(self, valor):
        self._contexto = self._contexto.__class__(self.cnx)
        self._contexto.set_cod_contexto(int(valor))

    cod_contexto = property(fget=get_cod_contexto, fset=set_cod_contexto)

    def get_pk(self):
        return self.get_cod_detalle_documento()

    def set_pk(self, *args):
        self.set_cod_detalle_documento(args[0])
        pass
