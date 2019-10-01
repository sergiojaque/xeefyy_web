#!/usr/bin/env python
# -*- coding: UTF8 -*-
'''Copyright (C) Victor Benitez
Generado:Version:1.6'''

from orm.xeeffyy.public.class_cuenta_balance import class_cuenta_balance
class cms_cuenta_balance(class_cuenta_balance):
    def __init__(self, cnx = None):
        class_cuenta_balance.__init__(self, cnx = cnx)
        
    def __unicode__(self):
        return str(self.get_desc_cuenta_balance())

    def __str__(self):
        return self.__unicode__()

    def set_filter_ec(self):
        #Se puede realizar los filtros necesarios para generar el EntryCompletion del Objeto
        #EJ:
        #self.set_cod_empresa(sys.__getattribute__('cod_empresa'))
        #   return True
        pass

    def _pre_save_db(self):
        #Se ejecuta antes de Guardar el Objeto en la BD
        #Si no corresponde:
        #raise Exception("Mensaje")
        pass
    def _post_save_db(self):
        #Se ejecuta despues de Guardar el Objeto en la BD
        #Si no corresponde:
        #raise Exception("Mensaje")
        pass
    def _pre_save(self):
        #Se ejecuta antes de Actualizar el Objeto en Momoria
        #Si no corresponde:
        #   return False,"Mensaje Error"
        return True,""
    def _post_save(self):
        #Se ejecuta despues de Guardar el Objeto en la BD
        #Si no corresponde:
        #   Return False,""
        return True,""
