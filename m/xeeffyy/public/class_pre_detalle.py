#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_pre_doc import cms_pre_doc as class_pre_doc
from orm.common_services.public.cms_cuenta_balance import cms_cuenta_balance as class_cuenta_balance
from orm.common_services.public.cms_cuenta_pcga import cms_cuenta_pcga as class_cuenta_pcga
from orm.common_services.public.cms_cuenta import cms_cuenta as class_cuenta
from lib_dev.pyBernateImp import *
import datetime
class class_pre_detalle(pyBernateImp):
    table='pre_detalle'
    schema='public'
    comment='pre detalle'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_pre_detalle=None
        self._desc_pre_detalle=None
        self._user_id=None
        self._pre_doc=class_pre_doc(cnx)
        self._valores=None
        self._cuenta_balance_2=class_cuenta_balance(cnx)
        self._cuenta_pcga_2=class_cuenta_pcga(cnx)
        self._cuenta_2=class_cuenta(cnx)
        self.map = {}
        self.map['cod_pre_detalle']= (1,'p',int,int(),True,True,64,False,'cod_pre_detalle','pkpre_detalle')
        self.map['desc_pre_detalle']= (2,'None',str,str(),True,False,10000,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_pre_doc']= (6,'None',int,int(),False,False,64,True,'cod_pre_doc','None')
        self.map['valores']= (7,'None',str,str(),False,False,None,True,'valores','None')
        self.map['cod_cuenta_balance_2']= (8,'None',int,int(),False,False,64,True,'cod_cuenta_balance_2','None')
        self.map['cod_cuenta_pcga_2']= (9,'None',int,int(),False,False,64,True,'cod_cuenta_pcga_2','None')
        self.map['cod_cuenta_2']= (10,'None',int,int(),False,False,64,True,'cod_cuenta_2','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.pre_detalle_cod_pre_detalle_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'pre_detalle'

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


    def get_cod_pre_detalle(self):
        return self._cod_pre_detalle

    def set_cod_pre_detalle(self, valor):
        self._cod_pre_detalle=int(valor)

    cod_pre_detalle = property(fget=get_cod_pre_detalle,fset=set_cod_pre_detalle)


    def get_desc_pre_detalle(self):
        return self._desc_pre_detalle

    def set_desc_pre_detalle(self, valor):
        self._desc_pre_detalle=str(valor)

    desc_pre_detalle = property(fget=get_desc_pre_detalle,fset=set_desc_pre_detalle)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_pre_doc(self):
        if self._pre_doc == self:
            self._pre_doc = self.__class__(self.cnx)
        if self._pre_doc._exists:
            return self._pre_doc
        else:
            r=self._pre_doc.get()
            self._pre_doc=r
            return r

    def set_pre_doc(self, valor):
        self._pre_doc=valor

    pre_doc = property(fget=get_pre_doc,fset=set_pre_doc)


    def get_cod_pre_doc(self):
        if self._pre_doc == self:
            self._pre_doc = self.__class__(self.cnx)
        return self._pre_doc.get_cod_pre_doc()

    def set_cod_pre_doc(self, valor):
        self._pre_doc = self._pre_doc.__class__(self.cnx)
        self._pre_doc.set_cod_pre_doc(int(valor))

    cod_pre_doc = property(fget=get_cod_pre_doc,fset=set_cod_pre_doc)


    def get_valores(self):
        return self._valores

    def set_valores(self, valor):
        self._valores=str(valor)

    valores = property(fget=get_valores,fset=set_valores)


    def get_cuenta_balance_2(self):
        if self._cuenta_balance_2 == self:
            self._cuenta_balance_2 = self.__class__(self.cnx)
        if self._cuenta_balance_2._exists:
            return self._cuenta_balance_2
        else:
            r=self._cuenta_balance_2.get()
            self._cuenta_balance_2=r
            return r

    def set_cuenta_balance_2(self, valor):
        self._cuenta_balance_2=valor

    cuenta_balance_2 = property(fget=get_cuenta_balance_2,fset=set_cuenta_balance_2)


    def get_cod_cuenta_balance_2(self):
        if self._cuenta_balance_2 == self:
            self._cuenta_balance_2 = self.__class__(self.cnx)
        return self._cuenta_balance_2.get_cod_cuenta_balance()

    def set_cod_cuenta_balance_2(self, valor):
        self._cuenta_balance_2 = self._cuenta_balance_2.__class__(self.cnx)
        self._cuenta_balance_2.set_cod_cuenta_balance(int(valor))

    cod_cuenta_balance_2 = property(fget=get_cod_cuenta_balance_2,fset=set_cod_cuenta_balance_2)


    def get_cuenta_pcga_2(self):
        if self._cuenta_pcga_2 == self:
            self._cuenta_pcga_2 = self.__class__(self.cnx)
        if self._cuenta_pcga_2._exists:
            return self._cuenta_pcga_2
        else:
            r=self._cuenta_pcga_2.get()
            self._cuenta_pcga_2=r
            return r

    def set_cuenta_pcga_2(self, valor):
        self._cuenta_pcga_2=valor

    cuenta_pcga_2 = property(fget=get_cuenta_pcga_2,fset=set_cuenta_pcga_2)


    def get_cod_cuenta_pcga_2(self):
        if self._cuenta_pcga_2 == self:
            self._cuenta_pcga_2 = self.__class__(self.cnx)
        return self._cuenta_pcga_2.get_cod_cuenta_pcga()

    def set_cod_cuenta_pcga_2(self, valor):
        self._cuenta_pcga_2 = self._cuenta_pcga_2.__class__(self.cnx)
        self._cuenta_pcga_2.set_cod_cuenta_pcga(int(valor))

    cod_cuenta_pcga_2 = property(fget=get_cod_cuenta_pcga_2,fset=set_cod_cuenta_pcga_2)


    def get_cuenta_2(self):
        if self._cuenta_2 == self:
            self._cuenta_2 = self.__class__(self.cnx)
        if self._cuenta_2._exists:
            return self._cuenta_2
        else:
            r=self._cuenta_2.get()
            self._cuenta_2=r
            return r

    def set_cuenta_2(self, valor):
        self._cuenta_2=valor

    cuenta_2 = property(fget=get_cuenta_2,fset=set_cuenta_2)


    def get_cod_cuenta_2(self):
        if self._cuenta_2 == self:
            self._cuenta_2 = self.__class__(self.cnx)
        return self._cuenta_2.get_cod_cuenta()

    def set_cod_cuenta_2(self, valor):
        self._cuenta_2 = self._cuenta_2.__class__(self.cnx)
        self._cuenta_2.set_cod_cuenta(int(valor))

    cod_cuenta_2 = property(fget=get_cod_cuenta_2,fset=set_cod_cuenta_2)


    def get_pk(self):
        return  self.get_cod_pre_detalle()
    def set_pk(self,*args):
        self.set_cod_pre_detalle(args[0])
        pass
