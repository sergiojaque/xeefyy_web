#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
from lib_dev.pyBernateImp import *
import datetime
class class_periodo(pyBernateImp):
    table='periodo'
    schema='public'
    comment='periodo'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_periodo=None
        self._desc_periodo=None
        self._user_id=None
        self._startdate=None
        self._enddate=None
        self._instant=None
        self.map = {}
        self.map['cod_periodo']= (1,'p',int,int(),True,True,64,False,'cod_periodo','pkperiodo')
        self.map['desc_periodo']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['startdate']= (6,'None',date,date(),False,False,None,True,'startdate','None')
        self.map['enddate']= (7,'None',date,date(),False,False,None,True,'enddate','None')
        self.map['instant']= (8,'None',date,date(),False,False,None,True,'instant','None')
        self.one2many = {}
        self._gen_pk="select nextval('public.periodo_cod_periodo_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'periodo'

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


    def get_cod_periodo(self):
        return self._cod_periodo

    def set_cod_periodo(self, valor):
        self._cod_periodo=int(valor)

    cod_periodo = property(fget=get_cod_periodo,fset=set_cod_periodo)


    def get_desc_periodo(self):
        return self._desc_periodo

    def set_desc_periodo(self, valor):
        self._desc_periodo=str(valor)

    desc_periodo = property(fget=get_desc_periodo,fset=set_desc_periodo)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_startdate(self):
        return self._startdate

    def set_startdate(self, valor):
        self._startdate=date(valor)

    startdate = property(fget=get_startdate,fset=set_startdate)


    def get_enddate(self):
        return self._enddate

    def set_enddate(self, valor):
        self._enddate=date(valor)

    enddate = property(fget=get_enddate,fset=set_enddate)


    def get_instant(self):
        return self._instant

    def set_instant(self, valor):
        self._instant=date(valor)

    instant = property(fget=get_instant,fset=set_instant)


    def get_pk(self):
        return  self.get_cod_periodo()
    def set_pk(self,*args):
        self.set_cod_periodo(args[0])
        pass
