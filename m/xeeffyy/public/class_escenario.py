#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_tipo_escenario import cms_tipo_escenario as class_tipo_escenario
from orm.common_services.public.cms_dimension import cms_dimension as class_dimension
from lib_dev.pyBernateImp import *
import datetime
class class_escenario(pyBernateImp):
    table='escenario'
    schema='public'
    comment='escenario'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_escenario=None
        self._desc_escenario=None
        self._user_id=None
        self._tipo_escenario=class_tipo_escenario(cnx)
        self._dimension=class_dimension(cnx)
        self.map = {}
        self.map['cod_escenario']= (1,'p',int,int(),True,True,64,False,'cod_escenario','pkescenario')
        self.map['desc_escenario']= (2,'None',str,str(),True,False,200,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_tipo_escenario']= (6,'None',int,int(),False,False,64,True,'cod_tipo_escenario','None')
        self.map['cod_dimension']= (7,'None',int,int(),False,False,64,True,'cod_dimension','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.escenario_cod_escenario_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'escenario'

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


    def get_cod_escenario(self):
        return self._cod_escenario

    def set_cod_escenario(self, valor):
        self._cod_escenario=int(valor)

    cod_escenario = property(fget=get_cod_escenario,fset=set_cod_escenario)


    def get_desc_escenario(self):
        return self._desc_escenario

    def set_desc_escenario(self, valor):
        self._desc_escenario=str(valor)

    desc_escenario = property(fget=get_desc_escenario,fset=set_desc_escenario)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_tipo_escenario(self):
        if self._tipo_escenario == self:
            self._tipo_escenario = self.__class__(self.cnx)
        if self._tipo_escenario._exists:
            return self._tipo_escenario
        else:
            r=self._tipo_escenario.get()
            self._tipo_escenario=r
            return r

    def set_tipo_escenario(self, valor):
        self._tipo_escenario=valor

    tipo_escenario = property(fget=get_tipo_escenario,fset=set_tipo_escenario)


    def get_cod_tipo_escenario(self):
        if self._tipo_escenario == self:
            self._tipo_escenario = self.__class__(self.cnx)
        return self._tipo_escenario.get_cod_tipo_escenario()

    def set_cod_tipo_escenario(self, valor):
        self._tipo_escenario = self._tipo_escenario.__class__(self.cnx)
        self._tipo_escenario.set_cod_tipo_escenario(int(valor))

    cod_tipo_escenario = property(fget=get_cod_tipo_escenario,fset=set_cod_tipo_escenario)


    def get_dimension(self):
        if self._dimension == self:
            self._dimension = self.__class__(self.cnx)
        if self._dimension._exists:
            return self._dimension
        else:
            r=self._dimension.get()
            self._dimension=r
            return r

    def set_dimension(self, valor):
        self._dimension=valor

    dimension = property(fget=get_dimension,fset=set_dimension)


    def get_cod_dimension(self):
        if self._dimension == self:
            self._dimension = self.__class__(self.cnx)
        return self._dimension.get_cod_dimension()

    def set_cod_dimension(self, valor):
        self._dimension = self._dimension.__class__(self.cnx)
        self._dimension.set_cod_dimension(int(valor))

    cod_dimension = property(fget=get_cod_dimension,fset=set_cod_dimension)


    def get_pk(self):
        return  self.get_cod_escenario()
    def set_pk(self,*args):
        self.set_cod_escenario(args[0])
        pass
