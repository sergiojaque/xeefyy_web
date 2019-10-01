#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from lib_dev.pyBernateImp import *
import datetime
class class_dd(pyBernateImp):
    table='dd'
    schema='public'
    comment='dd'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_dd=None
        self._desc_dd=None
        self._user_id=None
        self._cod=None
        self.map = {}
        self.map['cod_dd']= (1,'p',int,int(),True,True,64,False,'cod_dd','pkdd')
        self.map['desc_dd']= (2,'None',str,str(),True,False,None,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod']= (6,'None',int,int(),False,False,64,True,'cod','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.dd_cod_dd_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'dd'

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


    def get_cod_dd(self):
        return self._cod_dd

    def set_cod_dd(self, valor):
        self._cod_dd=int(valor)

    cod_dd = property(fget=get_cod_dd,fset=set_cod_dd)


    def get_desc_dd(self):
        return self._desc_dd

    def set_desc_dd(self, valor):
        self._desc_dd=str(valor)

    desc_dd = property(fget=get_desc_dd,fset=set_desc_dd)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_cod(self):
        return self._cod

    def set_cod(self, valor):
        self._cod=int(valor)

    cod = property(fget=get_cod,fset=set_cod)


    def get_pk(self):
        return  self.get_cod_dd()
    def set_pk(self,*args):
        self.set_cod_dd(args[0])
        pass
