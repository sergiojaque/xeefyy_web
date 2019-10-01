#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_cuenta import cms_cuenta as class_cuenta
from lib_dev.pyBernateImp import *
import datetime
class class_cuenta_pcga(pyBernateImp):
    table='cuenta_pcga'
    schema='public'
    comment='cuenta pcga'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_cuenta_pcga=None
        self._desc_cuenta_pcga=None
        self._user_id=None
        self._cuenta=class_cuenta(cnx)
        self.map = {}
        self.map['cod_cuenta_pcga']= (1,'p',int,int(),True,True,64,False,'cod_cuenta_pcga','pkcuenta_pcga')
        self.map['desc_cuenta_pcga']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_cuenta']= (6,'None',int,int(),False,False,64,True,'cod_cuenta','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.cuenta_pcga_cod_cuenta_pcga_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'cuenta_pcga'

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


    def get_cod_cuenta_pcga(self):
        return self._cod_cuenta_pcga

    def set_cod_cuenta_pcga(self, valor):
        self._cod_cuenta_pcga=int(valor)

    cod_cuenta_pcga = property(fget=get_cod_cuenta_pcga,fset=set_cod_cuenta_pcga)


    def get_desc_cuenta_pcga(self):
        return self._desc_cuenta_pcga

    def set_desc_cuenta_pcga(self, valor):
        self._desc_cuenta_pcga=str(valor)

    desc_cuenta_pcga = property(fget=get_desc_cuenta_pcga,fset=set_desc_cuenta_pcga)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_cuenta(self):
        if self._cuenta == self:
            self._cuenta = self.__class__(self.cnx)
        if self._cuenta._exists:
            return self._cuenta
        else:
            r=self._cuenta.get()
            self._cuenta=r
            return r

    def set_cuenta(self, valor):
        self._cuenta=valor

    cuenta = property(fget=get_cuenta,fset=set_cuenta)


    def get_cod_cuenta(self):
        if self._cuenta == self:
            self._cuenta = self.__class__(self.cnx)
        return self._cuenta.get_cod_cuenta()

    def set_cod_cuenta(self, valor):
        self._cuenta = self._cuenta.__class__(self.cnx)
        self._cuenta.set_cod_cuenta(int(valor))

    cod_cuenta = property(fget=get_cod_cuenta,fset=set_cod_cuenta)


    def get_pk(self):
        return  self.get_cod_cuenta_pcga()
    def set_pk(self,*args):
        self.set_cod_cuenta_pcga(args[0])
        pass
