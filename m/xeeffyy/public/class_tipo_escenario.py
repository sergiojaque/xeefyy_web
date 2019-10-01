#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from lib_dev.pyBernateImp import *
import datetime
class class_tipo_escenario(pyBernateImp):
    table='tipo_escenario'
    schema='public'
    comment='tipo escenario'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_tipo_escenario=None
        self._desc_tipo_escenario=None
        self._user_id=None
        self.map = {}
        self.map['cod_tipo_escenario']= (1,'p',int,int(),True,True,64,False,'cod_tipo_escenario','pktipo_escenario')
        self.map['desc_tipo_escenario']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.tipo_escenario_cod_tipo_escenario_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'tipo_escenario'

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


    def get_cod_tipo_escenario(self):
        return self._cod_tipo_escenario

    def set_cod_tipo_escenario(self, valor):
        self._cod_tipo_escenario=int(valor)

    cod_tipo_escenario = property(fget=get_cod_tipo_escenario,fset=set_cod_tipo_escenario)


    def get_desc_tipo_escenario(self):
        return self._desc_tipo_escenario

    def set_desc_tipo_escenario(self, valor):
        self._desc_tipo_escenario=str(valor)

    desc_tipo_escenario = property(fget=get_desc_tipo_escenario,fset=set_desc_tipo_escenario)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_pk(self):
        return  self.get_cod_tipo_escenario()
    def set_pk(self,*args):
        self.set_cod_tipo_escenario(args[0])
        pass
