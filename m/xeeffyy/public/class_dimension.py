#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from lib_dev.pyBernateImp import *
import datetime
class class_dimension(pyBernateImp):
    table='dimension'
    schema='public'
    comment='dimension'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_dimension=None
        self._desc_dimension=None
        self._user_id=None
        self.map = {}
        self.map['cod_dimension']= (1,'p',int,int(),True,True,64,False,'cod_dimension','pkdimension')
        self.map['desc_dimension']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.dimension_cod_dimension_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'dimension'

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


    def get_cod_dimension(self):
        return self._cod_dimension

    def set_cod_dimension(self, valor):
        self._cod_dimension=int(valor)

    cod_dimension = property(fget=get_cod_dimension,fset=set_cod_dimension)


    def get_desc_dimension(self):
        return self._desc_dimension

    def set_desc_dimension(self, valor):
        self._desc_dimension=str(valor)

    desc_dimension = property(fget=get_desc_dimension,fset=set_desc_dimension)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_pk(self):
        return  self.get_cod_dimension()
    def set_pk(self,*args):
        self.set_cod_dimension(args[0])
        pass
