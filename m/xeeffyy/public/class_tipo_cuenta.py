#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
try:
    from orm.common_services.public.cms_cuenta import cms_cuenta as class_cuenta
except:
    print 'cuenta no importable'
from lib_dev.pyBernateImp import *
import datetime
class class_tipo_cuenta(pyBernateImp):
    table='tipo_cuenta'
    schema='public'
    comment='tipo cuenta'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_tipo_cuenta=None
        self._user_id=None
        self._desc_tipo_cuenta=None
        self._cuentas=[]
        self.map = {}
        self.map['cod_tipo_cuenta']= (1,'p',int,int(),True,True,64,False,'cod_tipo_cuenta','pktipo_cuenta')
        self.map['user_id']= (4,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['desc_tipo_cuenta']= (5,'None',str,str(),True,False,100,True,'Observacion','None')
        self.one2many = {}
        self.one2many['cuenta']= (self.add_cuentas,'cuenta','tipo_cuenta')
        self._gen_pk="select nextval('public.tipo_cuenta_cod_tipo_cuenta_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'tipo_cuenta'

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


    def get_cod_tipo_cuenta(self):
        return self._cod_tipo_cuenta

    def set_cod_tipo_cuenta(self, valor):
        self._cod_tipo_cuenta=int(valor)

    cod_tipo_cuenta = property(fget=get_cod_tipo_cuenta,fset=set_cod_tipo_cuenta)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_desc_tipo_cuenta(self):
        return self._desc_tipo_cuenta

    def set_desc_tipo_cuenta(self, valor):
        self._desc_tipo_cuenta=str(valor)

    desc_tipo_cuenta = property(fget=get_desc_tipo_cuenta,fset=set_desc_tipo_cuenta)


    def add_cuentas(self):
        from orm.common_services.public.cms_cuenta import cms_cuenta
        self._cuentas.insert(0,cms_cuenta(self.cnx))
        if len(self._cuentas)>0:
            return self._cuentas[0]


    def del_cuentas(self,idx):
        if idx in range(0,len(self._cuentas)):
            del self._cuentas[idx]


    def get_cuentas(self,idx=None):
        if idx in range(0,len(self._cuentas)):
            return self._cuentas[idx]
        else:
            return self._cuentas


    def get_cuentas_db(self,order_by=None, where_adicional= None):
        from orm.common_services.public.cms_cuenta import cms_cuenta
        aux = cms_cuenta(self.cnx)
        aux.set_cod_tipo_cuenta(self.get_cod_tipo_cuenta())
        r = self.select_criterial(aux, order_by = order_by, where_adicional= where_adicional)
        self._cuentas = r


    def get_pk(self):
        return  self.get_cod_tipo_cuenta()
    def set_pk(self,*args):
        self.set_cod_tipo_cuenta(args[0])
        pass
