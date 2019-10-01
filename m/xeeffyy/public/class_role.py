#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
try:
    from orm.common_services.public.cms_role_cuenta import cms_role_cuenta as class_role_cuenta
except:
    print 'role_cuenta no importable'
from lib_dev.pyBernateImp import *
import datetime
import numpy as np


class class_role(pyBernateImp):
    table = 'role'
    schema = 'public'
    comment = 'role'

    def __init__(self, cnx=None):
        pyBernateImp.__init__(self, cnx)
        self._exists = False
        self._cod_role = None
        self._desc_role = None
        self._user_id = None
        self._role_cuentas = []
        self.map = {}
        self.map['cod_role'] = (1, 'p', int, int(), True, True, 64, False, 'cod_role', 'pkrole')
        self.map['desc_role'] = (2, 'None', str, str(), True, False, 100, True, 'Observacion', 'None')
        self.map['user_id'] = (5, 'None', str, str(), False, False, 50, True, 'user_id', 'None')
        self.one2many = {}
        self.one2many['role cuenta'] = (self.add_role_cuentas, 'role_cuenta', 'role')
        self._gen_pk = "select nextval('public.role_cod_role_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'role'

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

    def get_cod_role(self):
        return self._cod_role

    def set_cod_role(self, valor):
        self._cod_role = int(valor)

    cod_role = property(fget=get_cod_role, fset=set_cod_role)

    def get_desc_role(self):
        return self._desc_role

    def set_desc_role(self, valor):
        self._desc_role = str(valor)

    desc_role = property(fget=get_desc_role, fset=set_desc_role)

    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id = str(valor)

    user_id = property(fget=get_user_id, fset=set_user_id)

    def add_role_cuentas(self):
        from orm.common_services.public.cms_role_cuenta import cms_role_cuenta
        self._role_cuentas.insert(0, cms_role_cuenta(self.cnx))
        # if len(self._role_cuentas)>0:
        if len(np.array(self._role_cuentas)) > 0:
            return self._role_cuentas[0]

    def del_role_cuentas(self, idx):
        # if idx in range(0,len(self._role_cuentas)):
        if idx in np.arange(0, len(np.array(self._role_cuentas))):
            del self._role_cuentas[idx]

    def get_role_cuentas(self, idx=None):
        # if idx in range(0,len(self._role_cuentas)):
        if idx in np.arange(0, len(np.array(self._role_cuentas))):
            return self._role_cuentas[idx]
        else:
            return self._role_cuentas

    def get_role_cuentas_db(self, order_by=None, where_adicional=None):
        from orm.common_services.public.cms_role_cuenta import cms_role_cuenta
        aux = cms_role_cuenta(self.cnx)
        aux.set_cod_role(self.get_cod_role())
        r = self.select_criterial(aux, order_by=order_by, where_adicional=where_adicional)
        self._role_cuentas = r

    def get_pk(self):
        return self.get_cod_role()

    def set_pk(self, *args):
        self.set_cod_role(args[0])
        pass
