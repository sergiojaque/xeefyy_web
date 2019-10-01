#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''
Copyright (C) Victor Benitez
Generado:Version1.6
'''
try:
    from orm.common_services.public.cms_qry_data import cms_qry_data as class_qry_data
except:
    print 'qry_data no importable'
try:
    from orm.common_services.public.cms_qry_objects import cms_qry_objects as class_qry_objects
except:
    print 'qry_objects no importable'
from lib_dev.pyBernateImp import *
import datetime
class class_qry_cabecera(pyBernateImp):
    table='qry_cabecera'
    schema='public'
    comment='qry cabecera'
    def __init__(self, cnx = None):
        pyBernateImp.__init__(self, cnx)
        self._exists=False
        self._cod_qry_cabecera=None
        self._desc_qry_cabecera=None
        self._user_id=None
        self._obj_mr=None
        self._qry_datas=[]
        self._qry_objectss=[]
        self.map = {}
        self.map['cod_qry_cabecera']= (1,'p',int,int(),True,True,64,False,'cod_qry_cabecera','pkqry_cabecera')
        self.map['desc_qry_cabecera']= (2,'None',str,str(),True,False,100,True,'Observacion','None')
        self.map['user_id']= (5,'None',str,str(),False,False,50,True,'user_id','None')
        self.map['obj_mr']= (6,'None',str,str(),True,False,200,True,'obj_mr','None')
        self.one2many = {}
        self.one2many['qry data']= (self.add_qry_datas,'qry_data','qry_cabecera')
        self.one2many['qry objects']= (self.add_qry_objectss,'qry_objects','qry_cabecera')
        self._gen_pk="select nextval('public.qry_cabecera_cod_qry_cabecera_seq'::regclass)"

    def __str__(self):
        if self.get_pk() != None:
            return str(self.get_pk())
        else:
            return 'None'

    def __get__(self):
        return 'qry_cabecera'

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


    def get_cod_qry_cabecera(self):
        return self._cod_qry_cabecera

    def set_cod_qry_cabecera(self, valor):
        self._cod_qry_cabecera=int(valor)

    cod_qry_cabecera = property(fget=get_cod_qry_cabecera,fset=set_cod_qry_cabecera)


    def get_desc_qry_cabecera(self):
        return self._desc_qry_cabecera

    def set_desc_qry_cabecera(self, valor):
        self._desc_qry_cabecera=str(valor)

    desc_qry_cabecera = property(fget=get_desc_qry_cabecera,fset=set_desc_qry_cabecera)


    def get_user_id(self):
        return self._user_id

    def set_user_id(self, valor):
        self._user_id=str(valor)

    user_id = property(fget=get_user_id,fset=set_user_id)


    def get_obj_mr(self):
        return self._obj_mr

    def set_obj_mr(self, valor):
        self._obj_mr=str(valor)

    obj_mr = property(fget=get_obj_mr,fset=set_obj_mr)


    def add_qry_datas(self):
        from orm.common_services.public.cms_qry_data import cms_qry_data
        self._qry_datas.insert(0,cms_qry_data(self.cnx))
        if len(self._qry_datas)>0:
            return self._qry_datas[0]


    def del_qry_datas(self,idx):
        if idx in range(0,len(self._qry_datas)):
            del self._qry_datas[idx]


    def get_qry_datas(self,idx=None):
        if idx in range(0,len(self._qry_datas)):
            return self._qry_datas[idx]
        else:
            return self._qry_datas


    def get_qry_datas_db(self,order_by=None, where_adicional= None):
        from orm.common_services.public.cms_qry_data import cms_qry_data
        aux = cms_qry_data(self.cnx)
        aux.set_cod_qry_cabecera(self.get_cod_qry_cabecera())
        r = self.select_criterial(aux, order_by = order_by, where_adicional= where_adicional)
        self._qry_datas = r


    def add_qry_objectss(self):
        from orm.common_services.public.cms_qry_objects import cms_qry_objects
        self._qry_objectss.insert(0,cms_qry_objects(self.cnx))
        if len(self._qry_objectss)>0:
            return self._qry_objectss[0]


    def del_qry_objectss(self,idx):
        if idx in range(0,len(self._qry_objectss)):
            del self._qry_objectss[idx]


    def get_qry_objectss(self,idx=None):
        if idx in range(0,len(self._qry_objectss)):
            return self._qry_objectss[idx]
        else:
            return self._qry_objectss


    def get_qry_objectss_db(self,order_by=None, where_adicional= None):
        from orm.common_services.public.cms_qry_objects import cms_qry_objects
        aux = cms_qry_objects(self.cnx)
        aux.set_cod_qry_cabecera(self.get_cod_qry_cabecera())
        r = self.select_criterial(aux, order_by = order_by, where_adicional= where_adicional)
        self._qry_objectss = r


    def get_pk(self):
        return  self.get_cod_qry_cabecera()
    def set_pk(self,*args):
        self.set_cod_qry_cabecera(args[0])
        pass
