#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_tipo_cuenta import cms_tipo_cuenta as class_tipo_cuenta
from lib_dev.pyBernateImp import *
import datetime
class class_cuenta(pyBernateImp):
    table='cuenta'
    schema='public'
    comment='cuenta'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_cuenta=None
        self._desc_cuenta=None
        self._user_id=None
        self._tipo_cuenta=class_tipo_cuenta(cnx)
        self._etiqueta=None
        self.map = {}
        self.map['cod_cuenta']= (1,'p',int,int(),True,True,64,False,'cod_cuenta','pkcuenta')
        self.map['desc_cuenta']= (2,'None',str,str(),True,False,200,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_tipo_cuenta']= (6,'None',int,int(),False,False,64,True,'cod_tipo_cuenta','None')
        self.map['etiqueta']= (7,'None',str,str(),False,False,500,True,'etiqueta','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.cuenta_cod_cuenta_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'cuenta'

    def get(self):

        r=self.select_criterial(self,limit=1)
        if len(r)!=0:
            return r[0]
        else:
            return self


    def save(self):

        try:
            response = self._validate(self)
            if not response==True:
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


    def get_cod_cuenta(self):
        return self._cod_cuenta

    def set_cod_cuenta(self, valor):
        self._cod_cuenta=int(valor)

    cod_cuenta = property(fget=get_cod_cuenta,fset=set_cod_cuenta)


    def get_desc_cuenta(self):
        return self._desc_cuenta

    def set_desc_cuenta(self, valor):
        self._desc_cuenta=str(valor)

    desc_cuenta = property(fget=get_desc_cuenta,fset=set_desc_cuenta)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_tipo_cuenta(self):
        if self._tipo_cuenta == self:
            self._tipo_cuenta = self.__class__(self.cnx)
        if self._tipo_cuenta._exists:
            return self._tipo_cuenta
        else:
            r=self._tipo_cuenta.get()
            self._tipo_cuenta=r
            return r

    def set_tipo_cuenta(self, valor):
        self._tipo_cuenta=valor

    tipo_cuenta = property(fget=get_tipo_cuenta,fset=set_tipo_cuenta)


    def get_cod_tipo_cuenta(self):
        if self._tipo_cuenta == self:
            self._tipo_cuenta = self.__class__(self.cnx)
        return self._tipo_cuenta.get_cod_tipo_cuenta()

    def set_cod_tipo_cuenta(self, valor):
        self._tipo_cuenta = self._tipo_cuenta.__class__(self.cnx)
        self._tipo_cuenta.set_cod_tipo_cuenta(int(valor))

    cod_tipo_cuenta = property(fget=get_cod_tipo_cuenta,fset=set_cod_tipo_cuenta)


    def get_etiqueta(self):
        return self._etiqueta

    def set_etiqueta(self, valor):
        self._etiqueta=str(valor)

    etiqueta = property(fget=get_etiqueta,fset=set_etiqueta)


    def get_pk(self):
        return  self.get_cod_cuenta()
    def set_pk(self,*args):
        self.set_cod_cuenta(args[0])
        pass
