#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from lib_dev.pyBernateImp import *
import datetime
class class_unidad(pyBernateImp):
    table='unidad'
    schema='public'
    comment='unidad'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_unidad=None
        self._desc_unidad=None
        self._user_id=None
        self.map = {}
        self.map['cod_unidad']= (1,'p',int,int(),True,True,64,False,'cod_unidad','pkunidad')
        self.map['desc_unidad']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.unidad_cod_unidad_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'unidad'

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


    def get_cod_unidad(self):
        return self._cod_unidad

    def set_cod_unidad(self, valor):
        self._cod_unidad=int(valor)

    cod_unidad = property(fget=get_cod_unidad,fset=set_cod_unidad)


    def get_desc_unidad(self):
        return self._desc_unidad

    def set_desc_unidad(self, valor):
        self._desc_unidad=str(valor)

    desc_unidad = property(fget=get_desc_unidad,fset=set_desc_unidad)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_pk(self):
        return  self.get_cod_unidad()
    def set_pk(self,*args):
        self.set_cod_unidad(args[0])
        pass
