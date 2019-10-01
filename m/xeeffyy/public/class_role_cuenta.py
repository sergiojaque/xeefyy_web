#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_role import cms_role as class_role
from orm.common_services.public.cms_cuenta import cms_cuenta as class_cuenta
from lib_dev.pyBernateImp import *
import datetime
class class_role_cuenta(pyBernateImp):
    table='role_cuenta'
    schema='public'
    comment='role cuenta'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_role_cuenta=None
        self._desc_role_cuenta=None
        self._user_id=None
        self._role=class_role(cnx)
        self._cuenta=class_cuenta(cnx)
        self.map = {}
        self.map['cod_role_cuenta']= (1,'p',int,int(),True,True,64,False,'cod_role_cuenta','pkrole_cuenta')
        self.map['desc_role_cuenta']= (2,'None',str,str(),True,False,500,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_role']= (6,'None',int,int(),False,False,64,True,'cod_role','None')
        self.map['cod_cuenta']= (7,'None',int,int(),False,False,64,True,'cod_cuenta','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.role_cuenta_cod_role_cuenta_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'role_cuenta'

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


    def get_cod_role_cuenta(self):
        return self._cod_role_cuenta

    def set_cod_role_cuenta(self, valor):
        self._cod_role_cuenta=int(valor)

    cod_role_cuenta = property(fget=get_cod_role_cuenta,fset=set_cod_role_cuenta)


    def get_desc_role_cuenta(self):
        return self._desc_role_cuenta

    def set_desc_role_cuenta(self, valor):
        self._desc_role_cuenta=str(valor)

    desc_role_cuenta = property(fget=get_desc_role_cuenta,fset=set_desc_role_cuenta)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_role(self):
        if self._role == self:
            self._role = self.__class__(self.cnx)
        if self._role._exists:
            return self._role
        else:
            r=self._role.get()
            self._role=r
            return r

    def set_role(self, valor):
        self._role=valor

    role = property(fget=get_role,fset=set_role)


    def get_cod_role(self):
        if self._role == self:
            self._role = self.__class__(self.cnx)
        return self._role.get_cod_role()

    def set_cod_role(self, valor):
        self._role = self._role.__class__(self.cnx)
        self._role.set_cod_role(int(valor))

    cod_role = property(fget=get_cod_role,fset=set_cod_role)


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
        return  self.get_cod_role_cuenta()
    def set_pk(self,*args):
        self.set_cod_role_cuenta(args[0])
        pass
