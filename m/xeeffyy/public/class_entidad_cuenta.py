#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_entidad import cms_entidad as class_entidad
from orm.common_services.public.cms_cuenta import cms_cuenta as class_cuenta
from lib_dev.pyBernateImp import *
import datetime
class class_entidad_cuenta(pyBernateImp):
    table='entidad_cuenta'
    schema='public'
    comment='entidad cuenta'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_entidad_cuenta=None
        self._desc_entidad_cuenta=None
        self._user_id=None
        self._entidad=class_entidad(cnx)
        self._cuenta=class_cuenta(cnx)
        self.map = {}
        self.map['cod_entidad_cuenta']= (1,'p',int,int(),True,True,64,False,'cod_entidad_cuenta','pkentidad_cuenta')
        self.map['desc_entidad_cuenta']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_entidad']= (6,'None',str,str(),False,False,None,True,'cod_entidad','None')
        self.map['cod_cuenta']= (7,'None',int,int(),False,False,64,True,'cod_cuenta','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.entidad_cuenta_cod_entidad_cuenta_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'entidad_cuenta'

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


    def get_cod_entidad_cuenta(self):
        return self._cod_entidad_cuenta

    def set_cod_entidad_cuenta(self, valor):
        self._cod_entidad_cuenta=int(valor)

    cod_entidad_cuenta = property(fget=get_cod_entidad_cuenta,fset=set_cod_entidad_cuenta)


    def get_desc_entidad_cuenta(self):
        return self._desc_entidad_cuenta

    def set_desc_entidad_cuenta(self, valor):
        self._desc_entidad_cuenta=str(valor)

    desc_entidad_cuenta = property(fget=get_desc_entidad_cuenta,fset=set_desc_entidad_cuenta)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_entidad(self):
        if self._entidad == self:
            self._entidad = self.__class__(self.cnx)
        if self._entidad._exists:
            return self._entidad
        else:
            r=self._entidad.get()
            self._entidad=r
            return r

    def set_entidad(self, valor):
        self._entidad=valor

    entidad = property(fget=get_entidad,fset=set_entidad)


    def get_cod_entidad(self):
        if self._entidad == self:
            self._entidad = self.__class__(self.cnx)
        return self._entidad.get_cod_entidad()

    def set_cod_entidad(self, valor):
        self._entidad = self._entidad.__class__(self.cnx)
        self._entidad.set_cod_entidad(str(valor))

    cod_entidad = property(fget=get_cod_entidad,fset=set_cod_entidad)


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
        return  self.get_cod_entidad_cuenta()
    def set_pk(self,*args):
        self.set_cod_entidad_cuenta(args[0])
        pass
