#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_qry_cabecera import cms_qry_cabecera as class_qry_cabecera
from lib_dev.pyBernateImp import *
import datetime
class class_qry_data(pyBernateImp):
    table='qry_data'
    schema='public'
    comment='qry data'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_qry_data=None
        self._desc_qry_data=None
        self._user_id=None
        self._qry_cabecera=class_qry_cabecera(cnx)
        self._campo=None
        self._alias=None
        self._campor_orig=None
        self._suma=None
        self._label=None
        self._tabla=None
        self.map = {}
        self.map['cod_qry_data']= (1,'p',int,int(),True,True,64,False,'cod_qry_data','pkqry_data')
        self.map['desc_qry_data']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_qry_cabecera']= (6,'None',int,int(),False,False,64,True,'cod_qry_cabecera','None')
        self.map['campo']= (7,'None',str,str(),False,False,200,True,'campo','None')
        self.map['alias']= (8,'None',str,str(),False,False,200,True,'alias','None')
        self.map['campor_orig']= (9,'None',str,str(),False,False,200,True,'campor_orig','None')
        self.map['suma']= (10,'None',str,str(),False,False,1,True,'suma','None')
        self.map['label']= (11,'None',str,str(),False,False,200,True,'label','None')
        self.map['tabla']= (12,'None',str,str(),False,False,200,True,'tabla','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.qry_data_cod_qry_data_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'qry_data'

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


    def get_cod_qry_data(self):
        return self._cod_qry_data

    def set_cod_qry_data(self, valor):
        self._cod_qry_data=int(valor)

    cod_qry_data = property(fget=get_cod_qry_data,fset=set_cod_qry_data)


    def get_desc_qry_data(self):
        return self._desc_qry_data

    def set_desc_qry_data(self, valor):
        self._desc_qry_data=str(valor)

    desc_qry_data = property(fget=get_desc_qry_data,fset=set_desc_qry_data)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_qry_cabecera(self):
        if self._qry_cabecera == self:
            self._qry_cabecera = self.__class__(self.cnx)
        if self._qry_cabecera._exists:
            return self._qry_cabecera
        else:
            r=self._qry_cabecera.get()
            self._qry_cabecera=r
            return r

    def set_qry_cabecera(self, valor):
        self._qry_cabecera=valor

    qry_cabecera = property(fget=get_qry_cabecera,fset=set_qry_cabecera)


    def get_cod_qry_cabecera(self):
        if self._qry_cabecera == self:
            self._qry_cabecera = self.__class__(self.cnx)
        return self._qry_cabecera.get_cod_qry_cabecera()

    def set_cod_qry_cabecera(self, valor):
        self._qry_cabecera = self._qry_cabecera.__class__(self.cnx)
        self._qry_cabecera.set_cod_qry_cabecera(int(valor))

    cod_qry_cabecera = property(fget=get_cod_qry_cabecera,fset=set_cod_qry_cabecera)


    def get_campo(self):
        return self._campo

    def set_campo(self, valor):
        self._campo=str(valor)

    campo = property(fget=get_campo,fset=set_campo)


    def get_alias(self):
        return self._alias

    def set_alias(self, valor):
        self._alias=str(valor)

    alias = property(fget=get_alias,fset=set_alias)


    def get_campor_orig(self):
        return self._campor_orig

    def set_campor_orig(self, valor):
        self._campor_orig=str(valor)

    campor_orig = property(fget=get_campor_orig,fset=set_campor_orig)


    def get_suma(self):
        return self._suma

    def set_suma(self, valor):
        self._suma=str(valor)

    suma = property(fget=get_suma,fset=set_suma)


    def get_label(self):
        return self._label

    def set_label(self, valor):
        self._label=str(valor)

    label = property(fget=get_label,fset=set_label)


    def get_tabla(self):
        return self._tabla

    def set_tabla(self, valor):
        self._tabla=str(valor)

    tabla = property(fget=get_tabla,fset=set_tabla)


    def get_pk(self):
        return  self.get_cod_qry_data()
    def set_pk(self,*args):
        self.set_cod_qry_data(args[0])
        pass
