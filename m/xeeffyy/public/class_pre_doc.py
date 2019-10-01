#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from lib_dev.pyBernateImp import *
import datetime
class class_pre_doc(pyBernateImp):
    table='pre_doc'
    schema='public'
    comment='pre doc'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_pre_doc=None
        self._desc_pre_doc=None
        self._user_id=None
        self.map = {}
        self.map['cod_pre_doc']= (1,'p',int,int(),True,True,64,False,'cod_pre_doc','pkpre_doc')
        self.map['desc_pre_doc']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.pre_doc_cod_pre_doc_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'pre_doc'

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


    def get_cod_pre_doc(self):
        return self._cod_pre_doc

    def set_cod_pre_doc(self, valor):
        self._cod_pre_doc=int(valor)

    cod_pre_doc = property(fget=get_cod_pre_doc,fset=set_cod_pre_doc)


    def get_desc_pre_doc(self):
        return self._desc_pre_doc

    def set_desc_pre_doc(self, valor):
        self._desc_pre_doc=str(valor)

    desc_pre_doc = property(fget=get_desc_pre_doc,fset=set_desc_pre_doc)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_pk(self):
        return  self.get_cod_pre_doc()
    def set_pk(self,*args):
        self.set_cod_pre_doc(args[0])
        pass
