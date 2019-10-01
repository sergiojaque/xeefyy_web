#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_periodo import cms_periodo as class_periodo
from orm.common_services.public.cms_entidad import cms_entidad as class_entidad
from lib_dev.pyBernateImp import *
import datetime


class class_contexto(pyBernateImp):
    table = 'contexto'
    schema = 'public'
    comment = 'contexto'

    def __init__(self, cnx=None):
        pyBernateImp.__init__(self, cnx)
        self._exists = False
        self._cod_contexto = None
        self._desc_contexto = None
        self._user_id = None
        self._periodo = class_periodo(cnx)
        self._entidad = class_entidad(cnx)
        self.map = {}
        self.map['cod_contexto'] = (1, 'p', int, int(), True, True, 64, False, 'cod_contexto', 'pkcontexto')
        self.map['desc_contexto'] = (2, 'None', str, str(), True, False, 2000, True, 'Observacion', 'None')
        self.map['user_id'] = (5, 'None', str, str(), False, False, 50, True, 'user_id', 'None')
        self.map['cod_periodo'] = (6, 'None', int, int(), False, False, 64, True, 'cod_periodo', 'None')
        self.map['cod_entidad'] = (7, 'None', str, str(), False, False, None, True, 'cod_entidad', 'None')
        self.one2many = {}
        self._gen_pk = "select nextval('public.contexto_cod_contexto_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'contexto'

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

    def get_cod_contexto(self):
        return self._cod_contexto

    def set_cod_contexto(self, valor):
        self._cod_contexto = int(valor)

    cod_contexto = property(fget=get_cod_contexto, fset=set_cod_contexto)

    def get_desc_contexto(self):
        return self._desc_contexto

    def set_desc_contexto(self, valor):
        self._desc_contexto = str(valor)

    desc_contexto = property(fget=get_desc_contexto, fset=set_desc_contexto)

    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id = str(valor)

    user_id = property(fget=get_user_id, fset=set_user_id)

    def get_periodo(self):
        if self._periodo == self:
            self._periodo = self.__class__(self.cnx)
        if self._periodo._exists:
            return self._periodo
        else:
            r = self._periodo.get()
            self._periodo = r
            return r

    def set_periodo(self, valor):
        self._periodo = valor

    periodo = property(fget=get_periodo, fset=set_periodo)

    def get_cod_periodo(self):
        if self._periodo == self:
            self._periodo = self.__class__(self.cnx)
        return self._periodo.get_cod_periodo()

    def set_cod_periodo(self, valor):
        self._periodo = self._periodo.__class__(self.cnx)
        self._periodo.set_cod_periodo(int(valor))

    cod_periodo = property(fget=get_cod_periodo, fset=set_cod_periodo)

    def get_entidad(self):
        if self._entidad == self:
            self._entidad = self.__class__(self.cnx)
        if self._entidad._exists:
            return self._entidad
        else:
            r = self._entidad.get()
            self._entidad = r
            return r

    def set_entidad(self, valor):
        self._entidad = valor

    entidad = property(fget=get_entidad, fset=set_entidad)

    def get_cod_entidad(self):
        if self._entidad == self:
            self._entidad = self.__class__(self.cnx)
        return self._entidad.get_cod_entidad()

    def set_cod_entidad(self, valor):
        self._entidad = self._entidad.__class__(self.cnx)
        self._entidad.set_cod_entidad(str(valor))

    cod_entidad = property(fget=get_cod_entidad, fset=set_cod_entidad)

    def get_pk(self):
        return self.get_cod_contexto()

    def set_pk(self, *args):
        self.set_cod_contexto(args[0])
        pass
