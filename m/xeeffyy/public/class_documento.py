#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_entidad import cms_entidad as class_entidad

try:
    from orm.common_services.public.cms_detalle_documento import cms_detalle_documento as class_detalle_documento
except:
    print 'detalle_documento no importable'
from lib_dev.pyBernateImp import *
import datetime
import numpy as np


class class_documento(pyBernateImp):
    table = 'documento'
    schema = 'public'
    comment = 'documento'

    def __init__(self, cnx=None):
        pyBernateImp.__init__(self, cnx)
        self._exists = False
        self._cod_documento = None
        self._desc_documento = None
        self._user_id = None
        self._entidad = class_entidad(cnx)
        self._hash = None
        self._anio = None
        self._mes = None
        self._detalle_documentos = []
        self.map = {}
        self.map['cod_documento'] = (1, 'p', int, int(), True, True, 64, False, 'cod_documento', 'pkdocumento')
        self.map['desc_documento'] = (2, 'None', str, str(), True, False, 100, True, 'Observacion', 'None')
        self.map['user_id'] = (5, 'None', str, str(), False, False, 50, True, 'user_id', 'None')
        self.map['cod_entidad'] = (6, 'None', str, str(), False, False, None, True, 'cod_entidad', 'None')
        self.map['hash'] = (7, 'None', str, str(), False, False, None, True, 'hash', 'None')
        self.map['anio'] = (8, 'None', int, int(), False, False, 32, True, 'anio', 'None')
        self.map['mes'] = (9, 'None', int, int(), False, False, 32, True, 'mes', 'None')
        self.one2many = {}
        self.one2many['detalle documento'] = (self.add_detalle_documentos, 'detalle_documento', 'documento')
        self._gen_pk = "select nextval('public.documento_cod_documento_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
            # return np.dtype.str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'documento'

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

    def get_cod_documento(self):
        return self._cod_documento

    def set_cod_documento(self, valor):
        self._cod_documento = int(valor)

    cod_documento = property(fget=get_cod_documento, fset=set_cod_documento)

    def get_desc_documento(self):
        return self._desc_documento

    def set_desc_documento(self, valor):
        self._desc_documento = str(valor)

    desc_documento = property(fget=get_desc_documento, fset=set_desc_documento)

    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id = str(valor)

    user_id = property(fget=get_user_id, fset=set_user_id)

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

    def get_hash(self):
        return self._hash

    def set_hash(self, valor):
        self._hash = str(valor)

    hash = property(fget=get_hash, fset=set_hash)

    def get_anio(self):
        return self._anio

    def set_anio(self, valor):
        self._anio = int(valor)

    anio = property(fget=get_anio, fset=set_anio)

    def get_mes(self):
        return self._mes

    def set_mes(self, valor):
        self._mes = int(valor)

    mes = property(fget=get_mes, fset=set_mes)

    def add_detalle_documentos(self):
        from orm.common_services.public.cms_detalle_documento import cms_detalle_documento
        self._detalle_documentos.insert(0, cms_detalle_documento(self.cnx))
        # if len(self._detalle_documentos)
        if len(np.array(self._detalle_documentos)) > 0:
            return self._detalle_documentos[0]

    def del_detalle_documentos(self, idx):
        # if idx in range(0, len(self._detalle_documentos))
        if idx in np.arange(0, len(np.array(self._detalle_documentos))):
            del self._detalle_documentos[idx]

    def get_detalle_documentos(self, idx=None):
        #if idx in range(0, len(self._detalle_documentos))
        if idx in np.arange(0, len(np.array(self._detalle_documentos))):
            return self._detalle_documentos[idx]
        else:
            return self._detalle_documentos

    def get_detalle_documentos_db(self, order_by=None, where_adicional=None):
        from orm.common_services.public.cms_detalle_documento import cms_detalle_documento
        aux = cms_detalle_documento(self.cnx)
        aux.set_cod_documento(self.get_cod_documento())
        r = self.select_criterial(aux, order_by=order_by, where_adicional=where_adicional)
        self._detalle_documentos = r

    def get_pk(self):
        return self.get_cod_documento()

    def set_pk(self, *args):
        self.set_cod_documento(args[0])
        pass
