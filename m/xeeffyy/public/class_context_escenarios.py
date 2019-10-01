#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_contexto import cms_contexto as class_contexto
from orm.common_services.public.cms_escenario import cms_escenario as class_escenario
from lib_dev.pyBernateImp import *
import datetime
class class_context_escenarios(pyBernateImp):
    table='context_escenarios'
    schema='public'
    comment='context escenarios'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_context_escenarios=None
        self._desc_context_escenarios=None
        self._user_id=None
        self._contexto=class_contexto(cnx)
        self._escenario=class_escenario(cnx)
        self.map = {}
        self.map['cod_context_escenarios']= (1,'p',int,int(),True,True,64,False,'cod_context_escenarios','pkcontext_escenarios')
        self.map['desc_context_escenarios']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_contexto']= (6,'None',int,int(),False,False,64,True,'cod_contexto','None')
        self.map['cod_escenario']= (7,'None',int,int(),False,False,64,True,'cod_escenario','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.context_escenarios_cod_context_escenarios_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'context_escenarios'

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


    def get_cod_context_escenarios(self):
        return self._cod_context_escenarios

    def set_cod_context_escenarios(self, valor):
        self._cod_context_escenarios=int(valor)

    cod_context_escenarios = property(fget=get_cod_context_escenarios,fset=set_cod_context_escenarios)


    def get_desc_context_escenarios(self):
        return self._desc_context_escenarios

    def set_desc_context_escenarios(self, valor):
        self._desc_context_escenarios=str(valor)

    desc_context_escenarios = property(fget=get_desc_context_escenarios,fset=set_desc_context_escenarios)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_contexto(self):
        if self._contexto == self:
            self._contexto = self.__class__(self.cnx)
        if self._contexto._exists:
            return self._contexto
        else:
            r=self._contexto.get()
            self._contexto=r
            return r

    def set_contexto(self, valor):
        self._contexto=valor

    contexto = property(fget=get_contexto,fset=set_contexto)


    def get_cod_contexto(self):
        if self._contexto == self:
            self._contexto = self.__class__(self.cnx)
        return self._contexto.get_cod_contexto()

    def set_cod_contexto(self, valor):
        self._contexto = self._contexto.__class__(self.cnx)
        self._contexto.set_cod_contexto(int(valor))

    cod_contexto = property(fget=get_cod_contexto,fset=set_cod_contexto)


    def get_escenario(self):
        if self._escenario == self:
            self._escenario = self.__class__(self.cnx)
        if self._escenario._exists:
            return self._escenario
        else:
            r=self._escenario.get()
            self._escenario=r
            return r

    def set_escenario(self, valor):
        self._escenario=valor

    escenario = property(fget=get_escenario,fset=set_escenario)


    def get_cod_escenario(self):
        if self._escenario == self:
            self._escenario = self.__class__(self.cnx)
        return self._escenario.get_cod_escenario()

    def set_cod_escenario(self, valor):
        self._escenario = self._escenario.__class__(self.cnx)
        self._escenario.set_cod_escenario(int(valor))

    cod_escenario = property(fget=get_cod_escenario,fset=set_cod_escenario)


    def get_pk(self):
        return  self.get_cod_context_escenarios()
    def set_pk(self,*args):
        self.set_cod_context_escenarios(args[0])
        pass
