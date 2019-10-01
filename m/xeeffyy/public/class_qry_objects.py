#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from orm.common_services.public.cms_qry_cabecera import cms_qry_cabecera as class_qry_cabecera
from lib_dev.pyBernateImp import *
import datetime
class class_qry_objects(pyBernateImp):
    table='qry_objects'
    schema='public'
    comment='qry objects'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_qry_objects=None
        self._desc_qry_objects=None
        self._user_id=None
        self._qry_cabecera=class_qry_cabecera(cnx)
        self._x0=None
        self._y0=None
        self._x1=None
        self._y1=None
        self._cms=None
        self._x=None
        self._y=None
        self._campo=None
        self.map = {}
        self.map['cod_qry_objects']= (1,'p',int,int(),True,True,64,False,'cod_qry_objects','pkqry_objects')
        self.map['desc_qry_objects']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['cod_qry_cabecera']= (6,'None',int,int(),False,False,64,True,'cod_qry_cabecera','None')
        self.map['x0']= (7,'None',float,float(),True,False,10,True,'x0','None')
        self.map['y0']= (8,'None',float,float(),False,False,10,True,'y0','None')
        self.map['x1']= (9,'None',float,float(),False,False,10,True,'x1','None')
        self.map['y1']= (10,'None',float,float(),False,False,10,True,'y1','None')
        self.map['cms']= (11,'None',str,str(),False,False,200,True,'cms','None')
        self.map['x']= (12,'None',float,float(),False,False,10,True,'x','None')
        self.map['y']= (13,'None',float,float(),False,False,10,True,'y','None')
        self.map['campo']= (14,'None',str,str(),False,False,200,True,'campo','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.qry_objects_cod_qry_objects_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'qry_objects'

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


    def get_cod_qry_objects(self):
        return self._cod_qry_objects

    def set_cod_qry_objects(self, valor):
        self._cod_qry_objects=int(valor)

    cod_qry_objects = property(fget=get_cod_qry_objects,fset=set_cod_qry_objects)


    def get_desc_qry_objects(self):
        return self._desc_qry_objects

    def set_desc_qry_objects(self, valor):
        self._desc_qry_objects=str(valor)

    desc_qry_objects = property(fget=get_desc_qry_objects,fset=set_desc_qry_objects)


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


    def get_x0(self):
        return self._x0

    def set_x0(self, valor):
        self._x0=float(valor)

    x0 = property(fget=get_x0,fset=set_x0)


    def get_y0(self):
        return self._y0

    def set_y0(self, valor):
        self._y0=float(valor)

    y0 = property(fget=get_y0,fset=set_y0)


    def get_x1(self):
        return self._x1

    def set_x1(self, valor):
        self._x1=float(valor)

    x1 = property(fget=get_x1,fset=set_x1)


    def get_y1(self):
        return self._y1

    def set_y1(self, valor):
        self._y1=float(valor)

    y1 = property(fget=get_y1,fset=set_y1)


    def get_cms(self):
        return self._cms

    def set_cms(self, valor):
        self._cms=str(valor)

    cms = property(fget=get_cms,fset=set_cms)


    def get_x(self):
        return self._x

    def set_x(self, valor):
        self._x=float(valor)

    x = property(fget=get_x,fset=set_x)


    def get_y(self):
        return self._y

    def set_y(self, valor):
        self._y=float(valor)

    y = property(fget=get_y,fset=set_y)


    def get_campo(self):
        return self._campo

    def set_campo(self, valor):
        self._campo=str(valor)

    campo = property(fget=get_campo,fset=set_campo)


    def get_pk(self):
        return  self.get_cod_qry_objects()
    def set_pk(self,*args):
        self.set_cod_qry_objects(args[0])
        pass
