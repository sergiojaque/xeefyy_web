#!/usr/bin/env python
# -*- coding: UTF8 -*-
import decimal
import hashlib
import operator
import sys
from itertools import cycle

import requests
import xmltodict
from oauthlib.oauth2 import WebApplicationClient
from sqlalchemy.testing.pickleable import User

from form import RegisterForm
from pivot import pivot
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, flash, session, url_for, Blueprint, escape, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2 import connect
import psycopg2.extensions as _ext
from werkzeug.security import check_password_hash, generate_password_hash
import os
import zipfile
import xlrd
import tempfile
import urllib3
from datetime import datetime
import json
from flask_login import LoginManager, UserMixin, login_user, login_required
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

# dbdir = "sqlite:///" + "xeeffy.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://christian:1020@192.114.254.146/xeeffy'
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)

# app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db_user = os.environ.get('DBAAS_USER_NAME', 'christian')
# db_password = os.environ.get('DBAAS_USER_PASSWORD', '1020')
# db_connect = os.environ.get('DBAAS_DEFAULT_CONNECT_DESCRIPTOR', "190.114.254.146")
# service_port = port = os.environ.get('PORT', '5432')
POSTGRES_URL = "190.114.254.146:5432"
POSTGRES_USER = "christian"
POSTGRES_PW = "1020"
POSTGRES_DB = "xeeffy"

DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
                                                               db=POSTGRES_DB)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # silence the deprecation warning

db = SQLAlchemy(app)
cnx = connect(
    database='xeeffy',
    host='190.114.254.146',
    port='5432',
    user='christian',
    password='1020')

status = cnx.get_transaction_status()
if status == _ext.TRANSACTION_STATUS_UNKNOWN:
    # server connection lost
    cnx.close()
elif status != _ext.TRANSACTION_STATUS_IDLE:
    # connection in error or in transaction
    cnx.rollback()
db = SQLAlchemy(app)


class PoolError(psycopg2.Error):
    pass


# Configuration
GOOGLE_CLIENT_ID = os.environ.get("244753524041-5i7r3hop12h951t7rg1ob5mcd5cp6spk.apps.googleusercontent.com", None)
GOOGLE_CLIENT_SECRET = os.environ.get("5hmjxRqqNYiMfM8gCFcYSTcP", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
client = WebApplicationClient(GOOGLE_CLIENT_ID)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/login/google")
def loging():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/google/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(50), unique=True)
    contrasena = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    estado = db.column(db.Integer)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if cnx.status:
            username = request.form["username"]
            password = request.form["password"]
            user = Usuario.query.filter_by(usuario=username).first()
            if user and check_password_hash(user.contrasena, request.form["password"]):
                success_message = 'Bienvenido {}'.format(username)
                flash(success_message)
                session['username'] = username
                return redirect("/docEmpresa")
            else:
                error_message = 'usuario o contraseña no valido'
                flash(error_message)
            if not user or not check_password_hash(user.password, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('login'))
        else:
            flash("error al conectar bd")
            return redirect("/login")
    return render_template("/login.html")


@app.route('/', methods=["GET", "POST"])
def index():
    cursor = cnx.cursor()
    cursor.execute("select cod_perfil_entidad,desc_perfil_entidad from perfil_entidad where cod_perfil_entidad=1 ")
    usuario_xeeffy = cursor.fetchall()
    cursor.execute("select cod_perfil_entidad,desc_perfil_entidad from perfil_entidad where cod_perfil_entidad=2 ")
    empresa_financiar = cursor.fetchall()
    cursor.execute("select cod_perfil_entidad,desc_perfil_entidad from perfil_entidad where cod_perfil_entidad=3 ")
    relacionado = cursor.fetchall()
    cursor.execute("select cod_perfil_entidad,desc_perfil_entidad from perfil_entidad where cod_perfil_entidad=4 ")
    entidad_financiador = cursor.fetchall()
    return render_template("/index.html", usuario_xeeffy=usuario_xeeffy, empresa_financiar=empresa_financiar,
                           relacionado=relacionado, entidad_financiador=entidad_financiador)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    session.pop("username", None)
    session["username"] = "unknown"
    return redirect("/login")


@app.route("/signup/<cod_perfil_entidad>", methods=["GET", "POST"])
def signup(cod_perfil_entidad):
    cod_perfil_entidad = cod_perfil_entidad
    cursor = cnx.cursor()
    cursor.execute("""select *from perfil_entidad""")
    perfil_entidad = cursor.fetchall()
    if request.method == "POST":
        password1 = request.form["password1"]
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        if password == password1:
            hashed_pw = generate_password_hash(request.form["password"], method="sha256")
            new_user = Usuario(usuario=request.form["username"], contrasena=hashed_pw, email=email)
            user = Usuario.query.filter_by(email=email).first()
            cursor.execute("select usuario from usuario where usuario ='%s'" % (username))
            user_exist = cursor.fetchall()
            if user_exist != []:
                flash("usuario ya existe")
                return redirect('/signup/' + cod_perfil_entidad)
            if user:  # if a user is found, we want to redirect back to signup page so user can try again
                flash('Email address already exists')
                return redirect("/signup/" + cod_perfil_entidad)
            db.session.add(new_user)
            db.session.commit()
            cursor.execute("""update usuario set cod_perfil_entidad='%s' where usuario='%s'""" % (
                cod_perfil_entidad, username))
            cnx.commit()
        else:
            flash("contraseñas no coinsiden")
            return redirect('/signup/' + cod_perfil_entidad)
        return redirect("/login")
    return render_template("signup.html", perfil_entidad=perfil_entidad)


app.secret_key = "9;~X!cp4KhL9u}4#"


@app.route('/contacts')
def contacts():
    return render_template("/contacts.html")


@app.errorhandler(404)
def page_not_found(e):
    user = session.get("username")
    return render_template("/404.html", user=user)


@app.route('/analisis')
def analisis():
    return render_template("/analisis.html")


@app.before_request
def session_management():
    session.permanent = True


@app.route('/entidades', methods=["GET", "POST"])
def entidades():
    if session["username"] != 'unknown':
        cur = cnx.cursor()
        cur.execute("select * from entidad")
        data = cur.fetchall()
        return render_template("/entidades.html", dato=data)
    return redirect("login")


def validarRut(rut):
    rut = rut.upper();
    rut = rut.replace("-", "")
    rut = rut.replace(".", "")
    aux = rut[:-1]
    dv = rut[-1:]

    revertido = map(int, reversed(str(aux)))
    factors = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(revertido, factors))
    res = (-s) % 11

    if str(res) == dv:
        return True
    elif dv == "K" and res == 10:
        return True
    else:
        return False


@app.route('/formulario', methods=["POST"])
def formulario():
    rut_entidad = request.form['rut_empresa']
    rut_representante = request.form["rut_representante"]
    personalidad = request.form["update_empresa"]
    tipo_empresa = request.form["empresa1"]
    nombre_empresa = request.form["nombre_empresa"]
    nombre_representante = request.form["nombre_representante"]
    banco = request.form["banco"]
    banco = banco.replace(",]", "]")
    CMF = "NO"
    nivel1 = request.form["nivel1"]
    celular = request.form["celular"]
    if request.form["nivel1"] == "sopciom":
        nivel1 = 0
    else:
        nivel1 = request.form["nivel1"]
    nivel2 = request.form["nivel2"]
    if request.form["nivel2"] == "sopciom":
        nivel2 = 0
    else:
        nivel2 = request.form["nivel2"]
    nivel3 = request.form["nivel3"]
    if request.form["nivel3"] == "sopciom":
        nivel3 = 0
    else:
        nivel3 = request.form["nivel3"]

    nivel4 = request.form["nivel4"]
    if request.form["nivel4"] == "sopciom":
        nivel4 = 0
    else:
        nivel4 = request.form["nivel4"]
    nivel1 = int(nivel1)
    nivel2 = int(nivel2)
    nivel3 = int(nivel3)
    nivel4 = int(nivel4)
    region = request.form["region"]
    provincia = request.form["provincia"]
    comuna = request.form["comuna"]
    direccion = request.form["direccion"]
    cursor = cnx.cursor()
    rut_entidad = CRut(rut_entidad)
    validator = validarRut(rut_entidad)
    rut_representante = CRut(rut_representante)
    validator_representante = validarRut(rut_representante)
    if validator == True and validator_representante == True:
        rut_empresa = CRut(rut_entidad)
        cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad='%s'""" % (rut_empresa))
        test2 = cursor.fetchall()
        if test2 == []:
            cursor.execute(
                """insert into entidad (cod_entidad,desc_entidad,cod_tipo_entidad,rut_representante,nombre_representante,cod_actividad_nivel1,cod_actividad_nivel2,cod_actividad_nivel3,cod_actividad_nivel4,cmf,direccion,comuna_id,celular) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                (
                    rut_empresa, nombre_empresa, tipo_empresa, rut_representante, nombre_representante,
                    nivel1 if nivel1 else None,
                    nivel2 if nivel2 else None, nivel3 if nivel3 else None, nivel4 if nivel4 else None, CMF, direccion,
                    comuna, celular))
            for b in eval(banco):
                cursor.execute(
                    """insert into entidad_banco(desc_entidad_banco,cod_banco,cod_entidad) values ((select desc_banco from banco where cod_banco='%s'),'%s','%s')""" % (
                        b, b, rut_empresa))
            cnx.commit()
            success_message = 'Empresa Creada correctamente'
            flash(success_message)
            return redirect('/docEmpresa')
        if test2 != []:
            cursor.execute(
                """update entidad set desc_entidad=%s ,cod_tipo_entidad =%s, rut_representante = %s, nombre_representante=%s, cod_actividad_nivel1=%s,cod_actividad_nivel2=%s,cod_actividad_nivel3=%s,cod_actividad_nivel4=%s,cmf=%s,direccion=%s,comuna_id=%s,celular=%s where cod_entidad=%s""",
                (
                    nombre_empresa, tipo_empresa, rut_representante, nombre_representante, nivel1 if nivel1 else None,
                    nivel2 if nivel2 else None, nivel3 if nivel3 else None, nivel4 if nivel4 else None, CMF, direccion,
                    comuna, celular, rut_empresa))
            for b in eval(banco):
                cursor.execute(
                    """update entidad_banco set desc_entidad_banco=(select desc_banco from banco where cod_banco='%s'), cod_banco='%s', cod_entidad='%s'""" % (
                        b, b, rut_empresa))
            cnx.commit()
            success_message = 'Empresa Actualizada correctamente'
            flash(success_message)
            return redirect('/docEmpresa')
    success_message = 'error rut no valido'
    flash(success_message)
    return ("error rut no valido")


@app.route('/formulariocmf', methods=["POST"])
def formulariocmf():
    rut_entidad = request.form['rut_empresa']
    personalidad = request.form["update_empresa"]
    tipo_empresa = request.form["empresa1"]
    nombre_empresa = request.form["nombre_empresa"]
    banco = request.form["banco"]
    banco = banco.replace(",]", "]")
    CMF = "SI"
    nivel1 = request.form["nivel1"]
    if request.form["nivel1"] == "sopciom":
        nivel1 = 0
    else:
        nivel1 = request.form["nivel1"]
    nivel2 = request.form["nivel2"]
    if request.form["nivel2"] == "sopciom":
        nivel2 = 0
    else:
        nivel2 = request.form["nivel2"]
    nivel3 = request.form["nivel3"]
    if request.form["nivel3"] == "sopciom":
        nivel3 = 0
    else:
        nivel3 = request.form["nivel3"]

    nivel4 = request.form["nivel4"]
    if request.form["nivel4"] == "sopciom":
        nivel4 = 0
    else:
        nivel4 = request.form["nivel4"]
    nivel1 = int(nivel1)
    nivel2 = int(nivel2)
    nivel3 = int(nivel3)
    nivel4 = int(nivel4)
    region = request.form["region"]
    provincia = request.form["provincia"]
    comuna = request.form["comuna"]
    cursor = cnx.cursor()
    rut_entidad = CRut(rut_entidad)
    validator = validarRut(rut_entidad)
    if validator == True:
        rut_empresa = CRut(rut_entidad)
        cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad='%s'""" % (rut_empresa))
        test2 = cursor.fetchall()
        if test2 == []:
            cursor.execute(
                """insert into entidad (cod_entidad,desc_entidad,cod_tipo_entidad,cod_actividad_nivel1,cod_actividad_nivel2,cod_actividad_nivel3,cod_actividad_nivel4,cmf,comuna_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                (
                    rut_empresa, nombre_empresa, tipo_empresa, nivel1 if nivel1 else None,
                    nivel2 if nivel2 else None, nivel3 if nivel3 else None, nivel4 if nivel4 else None, CMF, comuna))
            # for b in eval(banco):
            #     cursor.execute(
            #         """insert into entidad_banco(desc_entidad_banco,cod_banco,cod_entidad) values ((select desc_banco from banco where cod_banco='%s'),'%s','%s')""" % (
            #             b, b, rut_empresa))
            cnx.commit()
            success_message = 'Empresa Creada correctamente'
            flash(success_message)
            return redirect('/docEmpresa')
        if test2 != []:
            cursor.execute(
                """update entidad set desc_entidad=%s ,cod_tipo_entidad =%s, cod_actividad_nivel1=%s,cod_actividad_nivel2=%s,cod_actividad_nivel3=%s,cod_actividad_nivel4=%s,cmf=%s,comuna_id=%s where cod_entidad=%s""",
                (
                    nombre_empresa, tipo_empresa, nivel1 if nivel1 else None,
                    nivel2 if nivel2 else None, nivel3 if nivel3 else None, nivel4 if nivel4 else None, CMF, comuna,
                    rut_empresa))
            # for b in eval(banco):
            #     cursor.execute(
            #         """update entidad_banco set desc_entidad_banco=(select desc_banco from banco where cod_banco='%s'), cod_banco='%s', cod_entidad='%s'""" % (
            #             b, b, rut_empresa))
            cnx.commit()
            success_message = 'Empresa Actualizada correctamente'
            flash(success_message)
            return redirect('/docEmpresa')
    success_message = 'error rut no valido'
    flash(success_message)
    return ("error rut no valido")


@app.route('/formularioEmpresaCMF/', methods=["GET", "POST"])
def formularioEmpresaCMF():
    if session["username"] != 'unknown':
        cursor = cnx.cursor()
        cursor.execute("select cod_clasificacion, desc_clasificacion from clasificacion")
        cl = cursor.fetchall()
        cursor.execute("select sector,desc_actividad_entidad from actividad_entidad where cod_nivel=1")
        lvl1 = cursor.fetchall()
        cursor.execute("select sector from actividad_entidad where cod_nivel=2")
        lvl2 = cursor.fetchall()
        cursor.execute("select sector from actividad_entidad where cod_nivel=3")
        lvl3 = cursor.fetchall()
        cursor.execute("select sector from actividad_entidad where cod_nivel=4")
        lvl4 = cursor.fetchall()
        cursor.execute("select cod_banco, desc_banco from banco")
        banco = cursor.fetchall()
        cursor.execute("select * from region")
        region = cursor.fetchall()
        cursor.execute("select * from provincia")
        provincia = cursor.fetchall()
        cursor.execute("select * from comuna")
        comuna = cursor.fetchall()
        return render_template("/formularioEmpresaCMF.html", region=region, comuna=comuna, provincia=provincia, cl=cl,
                               lvl1=lvl1, lvl2=lvl2, lvl3=lvl3, lvl4=lvl4,
                               banco=banco)
    return redirect("login")


@app.route('/formularioEmpresa/', methods=["GET", "POST"])
def formularioEmpresa():
    if session["username"] != 'unknown':
        cursor = cnx.cursor()
        cursor.execute("select cod_clasificacion, desc_clasificacion from clasificacion")
        cl = cursor.fetchall()
        cursor.execute("select sector,desc_actividad_entidad from actividad_entidad where cod_nivel=1")
        lvl1 = cursor.fetchall()
        cursor.execute("select sector from actividad_entidad where cod_nivel=2")
        lvl2 = cursor.fetchall()
        cursor.execute("select sector from actividad_entidad where cod_nivel=3")
        lvl3 = cursor.fetchall()
        cursor.execute("select sector from actividad_entidad where cod_nivel=4")
        lvl4 = cursor.fetchall()
        cursor.execute("select cod_banco, desc_banco from banco")
        banco = cursor.fetchall()
        cursor.execute("select * from region")
        region = cursor.fetchall()
        cursor.execute("select * from provincia")
        provincia = cursor.fetchall()
        cursor.execute("select * from comuna")
        comuna = cursor.fetchall()
        return render_template("/formularioEmpresa.html", region=region, comuna=comuna, provincia=provincia, cl=cl,
                               lvl1=lvl1, lvl2=lvl2, lvl3=lvl3, lvl4=lvl4,
                               banco=banco)
    return redirect("login")


@app.route('/tipoEmpresa/<cod_clasificacion>', methods=["GET", "POST"])
def tipoEmpresa(cod_clasificacion):
    cursor = cnx.cursor()
    cursor.execute("select cod_tipo_entidad, desc_tipo_entidad from tipo_entidad where cod_clasificacion = '%s'" % (
        cod_clasificacion))
    return jsonify(dictfetchall(cursor))


@app.route('/niveles/<cod_sector>/<cod_niveles>', methods=["GET", "POST"])
def niveles(cod_sector, cod_niveles):
    cursor = cnx.cursor()
    cursor.execute(
        "select * from actividad_entidad where cod_nivel ='%s' and substr(sector::text, 1, cod_nivel ) = '%s' order by desc_actividad_entidad" % (
            cod_niveles, cod_sector))
    # cursor.execute("select cod_nivel,desc_actividad_nivel,sector from actividad_nivel where sector='%s'" % (
    #     cod_niveles))
    return jsonify(dictfetchall(cursor))


@app.route('/regiones/<cod_niveles>', methods=["GET", "POST"])
def regiones(cod_niveles):
    cursor = cnx.cursor()
    cursor.execute(
        """SELECT
public.provincia.provincia_nombre,
public.provincia.provincia_id,
public.provincia.provincia_region_id,
public.region.region_nombre
FROM
public.provincia
INNER JOIN public.region ON public.provincia.provincia_region_id = public.region.region_id 
WHERE provincia.provincia_region_id ='%s' """ % (
            cod_niveles))
    return jsonify(dictfetchall(cursor))


@app.route('/provincias/<cod_niveles>', methods=["GET", "POST"])
def provincias(cod_niveles):
    cursor = cnx.cursor()
    cod_niveles = int(cod_niveles)
    cursor.execute(
        """SELECT
public.comuna.comuna_id,
public.comuna.comuna_nombre,
public.comuna.comuna_provincia_id,
public.provincia.provincia_nombre
FROM
public.provincia
INNER JOIN public.comuna ON public.comuna.comuna_provincia_id = public.provincia.provincia_id
WHERE comuna.comuna_provincia_id = '%s'""" % (
            cod_niveles))
    return jsonify(dictfetchall(cursor))


@app.route('/docEmpresa', methods=["GET", "POST"])
def docEmpresa():
    if session["username"] != 'unknown':
        m = 1
        cursor = cnx.cursor()
        cursor.execute("""select distinct * from entidad ORDER BY desc_entidad ASC""")
        enti = cursor.fetchall()
        if request.method == "POST":
            m = 0
            cursor = cnx.cursor()
            import urllib.request
            import urllib
            empresa = request.form["empresa"]
            empresa = empresa.upper()
            empresa1 = request.form["empresa1"]
            empresa1 = empresa1.upper()
            if empresa != '':
                cursor.execute("""select distinct * from entidad""")
                enti2 = cursor.fetchall()
                cursor.execute("""SELECT distinct
                public.entidad.cod_entidad,
                public.entidad.desc_entidad,
                public.documento.desc_documento,
                public.documento.anio,
                public.documento.mes,
                public.documento.cod_documento,
                public.documento.hash
                FROM
                public.documento
                INNER JOIN  public.entidad ON public.documento.cod_entidad = public.entidad.cod_entidad
                WHERE  documento.anio = '2017' and documento.mes ='12' and desc_entidad ilike '%s' order by desc_entidad DESC""" % (
                        '%' + empresa + '%'))
                data = cursor.fetchall()
                if data:
                    success_message = 'Empresa Encontrada'
                    flash(success_message)
                    return render_template("/docEmpresa.html", dato=data, m=m, enti=enti2)
                else:
                    success_message = 'Empresa no existe'
                    flash(success_message)
                    return redirect(url_for('docEmpresa'))
            if empresa1 != '' or empresa1 != '0':
                empresa1 = request.form["empresa1"]
                cursor.execute("""select distinct * from entidad""")
                enti1 = cursor.fetchall()
                cursor.execute("""SELECT DISTINCT
                                public.entidad.cod_entidad,
                                public.entidad.desc_entidad
                                FROM
                                public.documento
                                INNER JOIN public.entidad ON public.documento.cod_entidad = public.entidad.cod_entidad
                                WHERE desc_entidad ilike '%s'
                                ORDER BY desc_entidad DESC""" % ('%' + empresa1.upper() + '%'))
                data1 = cursor.fetchall()
                if data1 == []:
                    success_message = 'No tiene datos'
                    flash(success_message)
                    return redirect("/docEmpresa")
                if data1:
                    success_message = 'Empresa Encontrada'
                    flash(success_message)
                    return render_template("/docEmpresa.html", dato=data1, m=m, enti=enti1)
                else:
                    success_message = 'Empresa no existe'
                    flash(success_message)
                    return redirect(url_for('docEmpresa'))
        return render_template("/docEmpresa.html", m=m, enti=enti)
    return redirect("login")


@app.route('/industria', methods=["GET", "POST"])
def industria():
    if session["username"] != 'unknown':
        m = 1
        cursor = cnx.cursor()
        # cursor.execute("""select distinct * from entidad ORDER BY desc_entidad ASC""")
        cursor.execute("""SELECT distinct 
public.industria.desc_industria,
public.entidad.cod_industria
FROM
public.entidad
INNER JOIN public.industria ON public.entidad.cod_industria = public.industria.cod_industria""")
        enti = cursor.fetchall()
        if request.method == "POST":
            m = 0
            cursor = cnx.cursor()
            import urllib.request
            import urllib
            industria = request.form["industria"]
            cursor.execute("""select * from entidad where cod_industria ='%s'"""%(industria))
            ind = cursor.fetchall()
            if enti:
                success_message = 'Industria Encontrada'
                flash(success_message)
                return render_template("/industria.html", m=m,industria=industria,ind=ind)
            else:
                success_message = 'Empresa no existe'
                flash(success_message)
                return redirect(url_for('industria'))
        return render_template("/industria.html", m=m, enti=enti)
    return redirect("login")


@app.route('/ResumenIndustria/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def ResumenIndustria(cod_entidad, anio, mes):
    if session.get("username"):
        cursor = cnx.cursor()
        parametros = {'cod_entidad': cod_entidad}
        cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_industria =%(cod_entidad)s""",
                       parametros)
        rest = cursor.fetchall()
        cursor.execute("""select * from industria where cod_industria = '%s'"""%(cod_entidad))
        retail = cursor.fetchone()
        if not rest:
            abort(404)
        cursor.execute("""SELECT
                    public.entidad.cod_entidad,
                    public.entidad.desc_entidad,
                    public.documento.desc_documento,
                    public.documento.anio,
                    public.documento.mes,
                    public.documento.cod_documento,
                    public.documento.hash,
                    public.entidad.cod_industria
                    FROM
                    public.documento
                    INNER JOIN public.entidad ON public.documento.cod_entidad = public.entidad.cod_entidad
                    WHERE entidad.cod_industria = '%s'""" % (cod_entidad))
        entidadC = cursor.fetchall()

        # BALANCE
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='608' ORDER BY cod_entidad""" % (cod_entidad))
        corriente = cursor.fetchall()
        if corriente:
            corriente = corriente
        else:
            corriente = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='825' ORDER BY cod_entidad""" % (cod_entidad))
        Nocorriente = cursor.fetchall()
        if Nocorriente:
            Nocorriente = Nocorriente
        else:
            Nocorriente = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='808' ORDER BY cod_entidad""" % (
                cod_entidad))
        Total = cursor.fetchall()
        if Total:
            Total = Total
        else:
            Total = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='668' ORDER BY cod_entidad""" % (cod_entidad))
        corrientepasivo = cursor.fetchall()
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='809' ORDER BY cod_entidad""" % (cod_entidad))
        nocorrientepasivo = cursor.fetchall()
        if nocorrientepasivo:
            nocorrientepasivo = nocorrientepasivo
        else:
            nocorrientepasivo = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='681' ORDER BY cod_entidad""" % (cod_entidad))
        patrimonio = cursor.fetchall()
        if patrimonio:
            patrimonio = patrimonio
        else:
            patrimonio = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalanceindustrias where cod_industria = '%s' and cod_cuenta='754' ORDER BY cod_entidad""" % (
                cod_entidad))
        totalpasivo = cursor.fetchall()
        if totalpasivo:
            totalpasivo = totalpasivo
        else:
            totalpasivo = "n/a"
        # cursor.execute(
        #     """select * from resumen_PortadaEstructuraFinanciamiento where cod_entidad = '%s' and cod_cuenta='582'""" % (
        #         cod_entidad))
        # rest = cursor.fetchone()
        # if rest:
        #     D1 = rest[9]
        # else:
        #     D1 = 1
        # cursor.execute(
        #     """select * from resumen_PortadaEstructuraFinanciamiento where cod_entidad = '%s' and cod_cuenta='791' """ % (
        #         cod_entidad))
        # rest = cursor.fetchone()
        # if rest:
        #     D2 = rest[9]
        # else:
        #     D2 = 1
        # if D1 == 1 or D2 == 1:
        #     Deudor = "n/a"
        # else:
        #     Deudor = (D1 + D2)
        # cursor.execute(
        #     """select * from resumen_PortadaEstructuraFinanciamiento where cod_entidad = '%s' and cod_cuenta='681'""" % (
        #         cod_entidad))
        # rest = cursor.fetchone()
        # if rest:
        #     Capital = rest[9]
        # else:
        #     Capital = "n/a"
        # if Capital == "n/a" or Deudor == "n/a":
        #     porcientodeuda = "n/a"
        #     porcientoCapital = "n/a"
        #     testructura = "n/a"
        # else:
        #     testructura = (Deudor + Capital)
        #     porcientodeuda = (Deudor / testructura) * 100
        #     porcientoCapital = (Capital / testructura) * 100
        # RATIOS
        data3, columnas3 = get_portadaratiosddindustria(cod_entidad, anio, mes)
        # EERR
        data4, columnas4 = get_portadaeresultadoindustria(cod_entidad, anio, mes)
        return render_template("/ResumenIndustria.html",
                               corriente=corriente, Nocorriente=Nocorriente, Total=Total,
                               corrientepasivo=corrientepasivo, nocorrientepasivo=nocorrientepasivo,
                               totalpasivo=totalpasivo, data3=data3,
                               columnas3=columnas3, data4=list(data4), columnas4=columnas4, entidadC=entidadC,
                               patrimonio=patrimonio,retail=retail)
    return redirect("/login")

def get_balanceindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Efectivo y equivalentes al efectivo'] = "(float(a.get(739,1)))  if  (a.get(739,0))  else 0"
    RATIOS[
        'Otros activos financieros corrientes'] = "(float(a.get(607,1)))  if  a.get(607,0)  else 0"
    RATIOS[
        'Otros activos no financieros corrientes'] = "(float(a.get(835,1)))  if  a.get(835,0)  else 0"
    RATIOS[
        'Deudores comerciales y otras cuentas por cobrar corrientes'] = "(float(a.get(775,1)))  if  a.get(775,0)  else 0"
    RATIOS[
        'Cuentas por cobrar a entidades relacionadas, corrientes'] = "(float(a.get(787,1)))  if  a.get(787,0)  else 0"
    RATIOS[
        'Inventarios corrientes'] = "(float(a.get(695,1)))  if  a.get(695,0)  else 0"
    RATIOS[
        'Activos biológicos corrientes'] = "(float(a.get(1290,1)))  if  a.get(1290,0)  else 0"
    RATIOS[
        'Activos por impuestos corrientes, corrientes'] = "(float(a.get(481,1)))  if  a.get(481,0)  else 0"
    RATIOS[
        'Total de activos corrientes distintos de los activo o grupos de activos'] = "(float(a.get(797,1)))  if  a.get(797,0)  else 0"
    RATIOS[
        'Activos no corrientes o grupos de activos para su disposición clasificados'] = "(float(a.get(1291,1)))  if  a.get(1291,0)  else 0"
    RATIOS[
        'Activos corrientes totales'] = "(float(a.get(608,1)))  if  a.get(608,0)  else 0"
    RATIOS[
        'Otros activos financieros no corrientes'] = "(float(a.get(520,1)))  if  a.get(520,0)  else 0"
    RATIOS[
        'Otros activos no financieros no corrientes'] = "(float(a.get(462,1)))  if  a.get(462,0)  else 0"
    RATIOS[
        'Cuentas por cobrar no corrientes'] = "(float(a.get(753,1)))  if  a.get(753,0)  else 0"
    RATIOS[
        'Cuentas por cobrar a entidades relacionadas, no corrientes'] = "(float(a.get(680,1)))  if  a.get(680,0)  else 0"
    RATIOS[
        'Inversiones contabilizadas utilizando el método de la participación'] = "(float(a.get(713,1)))  if  a.get(713,0)  else 0"
    RATIOS[
        'Activos intangibles distintos de la plusvalía'] = "(float(a.get(748,1)))  if  a.get(748,0)  else 0"
    RATIOS[
        'Plusvalía'] = "(float(a.get(866,1)))  if  a.get(866,0)  else 0"
    RATIOS[
        'Propiedades, planta y equipo'] = "(float(a.get(456,1)))  if  a.get(456,0)  else 0"
    RATIOS[
        'Activos biológicos no corrientes'] = "(float(a.get(1294,1)))  if  a.get(1294,0)  else 0"
    RATIOS[
        'Propiedad de inversión'] = "(float(a.get(581,1)))  if  a.get(581,0)  else 0"
    RATIOS[
        'Activos por impuestos diferidos'] = "(float(a.get(622,1)))  if  a.get(622,0)  else 0"
    RATIOS[
        'Total de activos no corrientes'] = "(float(a.get(825,1)))  if  a.get(825,0)  else 0"
    RATIOS[
        'Total de activos'] = "(float(a.get(808,1)))  if  a.get(808,0)  else 0"
    RATIOS[
        'Otros pasivos financieros corrientes'] = "(float(a.get(582,1)))  if  a.get(582,0)  else 0"
    RATIOS[
        'Cuentas por pagar comerciales y otras cuentas por pagar'] = "(float(a.get(783,1)))  if  a.get(783,0)  else 0"
    RATIOS[
        'Cuentas por pagar a entidades relacionadas, corrientes'] = "(float(a.get(461,1)))  if  a.get(461,0)  else 0"
    RATIOS[
        'Otras provisiones a corto plazo'] = "(float(a.get(659,1)))  if  a.get(659,0)  else 0"
    RATIOS[
        'Pasivos por impuestos corrientes, corrientes'] = "(float(a.get(477,1)))  if  a.get(477,0)  else 0"
    RATIOS[
        'Provisiones corrientes por beneficios a los empleados'] = "(float(a.get(756,1)))  if  a.get(756,0)  else 0"
    RATIOS[
        'Otros pasivos no financieros corrientes'] = "(float(a.get(621,1)))  if  a.get(621,0)  else 0"
    RATIOS[
        'Total de pasivos corrientes distintos de los pasivos incluidos'] = "(float(a.get(745,1)))  if  a.get(745,0)  else 0"
    RATIOS[
        'Pasivos corrientes totales'] = "(float(a.get(668,1)))  if  a.get(688,0)  else 0"
    RATIOS[
        'Otros pasivos financieros no corrientes'] = "(float(a.get(791,1)))  if  a.get(791,0)  else 0"
    RATIOS[
        'Cuentas por pagar no corrientes'] = "(float(a.get(822,1)))  if  a.get(822,0)  else 0"
    RATIOS[
        'Cuentas por pagar a entidades relacionadas, no corrientes'] = "(float(a.get(486,1)))  if  a.get(486,0)  else 0"
    RATIOS[
        'Otras provisiones a largo plazo'] = "(float(a.get(524,1)))  if  a.get(524,0)  else 0"
    RATIOS[
        'Pasivo por impuestos diferidos'] = "(float(a.get(640,1)))  if  a.get(640,0)  else 0"
    RATIOS[
        'Provisiones no corrientes por beneficios a los empleados'] = "(float(a.get(629,1)))  if  a.get(629,0)  else 0"
    RATIOS[
        'Otros pasivos no financieros no corrientes'] = "(float(a.get(633,1)))  if  a.get(633,0)  else 0"
    RATIOS[
        'Total de pasivos no corrientes'] = "(float(a.get(809,1)))  if  a.get(809,0)  else 0"
    RATIOS[
        'Total de pasivos'] = "(float(a.get(519,1)))  if  a.get(519,0)  else 0"
    RATIOS[
        'Capital emitido'] = "(float(a.get(859,1)))  if  a.get(859,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) acumuladas'] = "(float(a.get(670,1)))  if  a.get(670,0)  else 0"
    RATIOS[
        'Prima de emisión'] = "(float(a.get(939,1)))  if  a.get(939,0)  else 0"
    RATIOS[
        'Acciones propias en cartera'] = "(float(a.get(1303,1)))  if  a.get(1303,0)  else 0"
    RATIOS[
        'Otras participaciones en el patrimonio'] = "(float(a.get(1304,1)))  if  a.get(1304,0)  else 0"
    RATIOS[
        'Otras reservas'] = "(float(a.get(789,1)))  if  a.get(789,0)  else 0"
    RATIOS[
        'Patrimonio atribuible a los propietarios de la controladora'] = "(float(a.get(879,1)))  if  a.get(879,0)  else 0"
    RATIOS[
        'Participaciones no controladoras'] = "(float(a.get(620,1)))  if  a.get(620,0)  else 0"
    RATIOS[
        'Patrimonio total'] = "(float(a.get(681,1)))  if  a.get(681,0)  else 0"
    RATIOS[
        'Total de patrimonio y pasivos'] = "(float(a.get(754,1)))  if  a.get(754,0)  else 0"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_balanceindustria  where cod_industria = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_industria ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_balanceindustria  where cod_industria = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["BALANCE"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][2])
            a = dict()
            for r in resumen:
                a[r[5]] = r[10]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
        b = a
    return RESULTADO.values(), COLUMNAS


@app.route('/balanceindustria/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def balanceindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_industria =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        data1, columnas1 = get_balanceindustria(cod_entidad, anio, mes)
        return render_template("/balanceindustria.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad)
    data, columnas = get_balanceindustria(cod_entidad, anio, mes)
    return render_template("/balanceindustria.html", entidad=entidad, data=list(data),
                           columnas=columnas, cod_entidad=cod_entidad)


# funcion extraccion ratios
def get_analisis_relativoindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    aniom = int(anio) - 1
    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades'] = "(float(a.get(540,0)) / float(a.get(540,0))*100) if (a.get(540,0) and a.get(540,0)) else 0"
    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)) / float(a.get(540,1))*100) if (a.get(727,0) and a.get(540,0)) else 0"
    RATIOS[
        'Otros Ingresos'] = "(float(a.get(682,0)) / float(a.get(540,0))*100) if (a.get(682,0) and a.get(540,0)) else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,0)) / float(a.get(540,0))*100) if (a.get(1324,0) and a.get(540,0)) else 0"
    RATIOS[
        'Gastos Administracion'] = "(float(a.get(618,0)) / float(a.get(540,0))*100) if (a.get(618,0) and a.get(540,0)) else 0"
    RATIOS[
        'Otros Gastos'] = "(float(a.get(815,0)) / float(a.get(540,0))*100) if (a.get(815,0) and a.get(540,0)) else 0"
    RATIOS[
        'Otras Ganancias'] = "(float(a.get(1325,0)) / float(a.get(540,0))*100) if (a.get(1325,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias'] = "(float(a.get(817,0)) / float(a.get(540,0))*100) if (a.get(817,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Que Surgen'] = "(float(a.get(1326,0)) / float(a.get(540,0))*100) if (a.get(1326,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ingresos Financieros'] = "(float(a.get(558,0)) / float(a.get(540,0))*100) if (a.get(558,0) and a.get(540,0)) else 0"
    RATIOS[
        'Costos Financieros'] = "(float(a.get(764,0)) / float(a.get(540,0))*100) if (a.get(764,0) and a.get(540,0)) else 0"
    RATIOS[
        'Deterioro de Valor'] = "(float(a.get(9744,0)) / float(a.get(540,0))*100) if (a.get(9744,0) and a.get(540,0)) else 0"
    RATIOS[
        'Diferencias de Cambio'] = "(float(a.get(849,0)) / float(a.get(540,0))*100) if (a.get(849,0) and a.get(540,0)) else 0"
    RATIOS[
        'Resultados por Unidades'] = "(float(a.get(516,0)) / float(a.get(540,0))*100) if (a.get(516,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias de Cobertura'] = "(float(a.get(10377,0)) / float(a.get(540,0))*100) if (a.get(10377,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Antes del Impuesto'] = "(float(a.get(788,0)) / float(a.get(540,0))*100) if (a.get(788,0) and a.get(540,0)) else 0"
    RATIOS[
        'Gastos por Impuestos a las Ganancias'] = "(float(a.get(476,0)) / float(a.get(540,0))*100) if (a.get(476,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Procedentes Continuada'] = "(float(a.get(774,0)) / float(a.get(540,0))*100) if (a.get(774,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Porcentes Discontinuas'] = "(float(a.get(1328,0)) / float(a.get(540,0))*100) if (a.get(1328,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancia (Perdida)'] = "(float(a.get(479,0)) / float(a.get(540,0))*100) if (a.get(479,0) and a.get(540,0)) else 0"

    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from analisis_relativoindustria  where cod_industria = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_industria ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from analisis_relativoindustria  where cod_industria = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["ESTADO RESULTADO"]
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][2])
            a = dict()
            for r in resumen:
                a[r[5]] = r[10]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    return RESULTADO.values(), COLUMNAS


# pagina estados de resutlados
@app.route('/analisisrelativoindustria/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def analisisrelativoindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_industria =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        data1, columnas1 = get_analisis_relativoindustria(cod_entidad, anio, mes)
        return render_template("/analisisrelativoindustria.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad)
    data, columnas = get_analisis_relativoindustria(cod_entidad, anio, mes)
    return render_template("/analisisrelativoindustria.html", entidad=entidad, data=list(data), columnas=columnas,
                           cod_entidad=cod_entidad)

# pagina estados de resutlados
@app.route('/eresultadoindustria/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def eresultadoindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_industria =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        data1, columnas1 = get_eresultado(cod_entidad, anio, mes)
        return render_template("/eresultadoindustria.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad)
    data, columnas = get_eresultadoindustria(cod_entidad, anio, mes)
    return render_template("/eresultadoindustria.html", entidad=entidad, data=list(data), columnas=columnas,
                           cod_entidad=cod_entidad)


def get_eresultadoindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades ordinarias'] = "(float(a.get(540,1)))  if  (a.get(540,0))  else 0"
    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)))  if  a.get(727,0)  else 0"
    RATIOS[
        'Ganancias Bruta'] = "(float(a.get(805,1)))  if  a.get(805,0)  else 0"
    RATIOS[
        'Otros Ingresos'] = "(float(a.get(682,1)))  if  a.get(682,0)  else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,1)))  if  a.get(1324,0)  else 0"
    RATIOS[
        'Gastos de administración'] = "(float(a.get(618,1)))  if  a.get(618,0)  else 0"
    RATIOS[
        'Otros gastos, por función'] = "(float(a.get(1325,1)))  if  a.get(1325,0)  else 0"
    RATIOS[
        'Otras ganancias (pérdidas)'] = "(float(a.get(815,1)))  if  a.get(815,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) de actividades operacionales'] = "(float(a.get(817,1)))  if  a.get(817,0)  else 0"
    RATIOS[
        'Ingresos financieros'] = "(float(a.get(558,1)))  if  a.get(558,0)  else 0"
    RATIOS[
        'Costos financieros'] = "(float(a.get(764,1)))  if  a.get(764,0)  else 0"
    RATIOS[
        'Participación en las ganancias (pérdidas) de asociadas y negocios'] = "(float(a.get(824,1)))  if  a.get(824,0)  else 0"
    RATIOS[
        'Diferencias de cambio'] = "(float(a.get(849,1)))  if  a.get(849,0)  else 0"
    RATIOS[
        'Resultados por unidades de reajuste'] = "(float(a.get(516,1)))  if  a.get(516,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) que surgen de diferencias entre importes en libros'] = "(float(a.get(1327,1)))  if  a.get(1327,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), antes de impuestos'] = "(float(a.get(788,1)))  if  a.get(788,0)  else 0"
    RATIOS[
        'Gasto por impuestos a las ganancias'] = "(float(a.get(476,1)))  if  a.get(476,0)  else 0"
    RATIOS[
        'Ganancia (pérdida) procedente de operaciones continuadas'] = "(float(a.get(774,1)))  if  a.get(774,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), atribuible a los propietarios de la controladora'] = "(float(a.get(704,1)))  if  a.get(704,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), atribuible a participaciones no controladoras'] = "(float(a.get(868,1)))  if  a.get(868,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_eerrindustria  where cod_industria = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_industria ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_eerrindustria  where cod_industria = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["ESTADO RESULTADO"]
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][2])
            a = dict()
            for r in resumen:
                a[r[5]] = r[10]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    return RESULTADO.values(), COLUMNAS


@app.route('/industriaratiosdd/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def industriaratiosdd(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_industria =%(cod_entidad)s""", parametros)
    rest = cursor.fetchall()
    if not rest:
        abort(404)
    entidad = rest[1]
    empresa = request.args.get("empresa")
    if request.args.get("mes"):
        mes = request.args.get("mes")
        if empresa != None:
            cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
            en = cursor.fetchone()[1]
            data1, columnas1 = get_ratiosindustria(cod_entidad, anio, mes)
            return render_template("/industriaratiosdd.html", entidad=entidad, data=list(data1),
                                   columnas1=columnas1,
                                   data1=list(data1), en=en, empresa=empresa, cod_entidad=cod_entidad)
        data1, columnas1 = get_ratiosindustria(cod_entidad, anio, mes)
        return render_template("/industriaratiosdd.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad, empresa=empresa)
    data, columnas = get_ratiosindustria(cod_entidad, anio, mes)
    return render_template("/industriaratiosdd.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa,
                           cod_entidad=cod_entidad,rest=rest)


# funcion extraccion ratios
def get_ratiosindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    aniom = int(anio) - 1
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS['Liquidez'] = "(float(a.get(608,1)) / float(a.get(668,1))) if (a.get(608,0) and a.get(668,0)) else 0"
    RATIOS[
        'Prueba Acida'] = "(float(a.get(608,0)) - float(a.get(695,0))) / float(a.get(668,0)) if (a.get(608,0) and a.get(668,0) and a.get(695,0)) else 0"
    RATIOS[
        'Dias De Cobro'] = "float(a.get(775) or 0) / (float(a.get(540) or 0) * float(1.19))* 365 if (a.get(775,0) and a.get(540,0)) else 0"
    RATIOS[
        'Dias De Pago'] = "((float(a.get(783) or 0)) / (float(a.get(727) or 0) + float(a.get(695) or 0) - float(b.get(695) or 0)))*365 if (a.get(783,0) and a.get(727,0)and b.get(695,0)) else 0"
    RATIOS[
        'Dias De Existencia'] = "((float(a.get(695) or 0) / float(a.get(727) or 0)) * float(365)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'ROI'] = "(float(a.get(479) or 0) / float(a.get(808) or 0)*100) if (a.get(479,0) and a.get(808,0)) else 0"
    RATIOS[
        'ROE'] = "(float(a.get(479) or 0) / float(a.get(681) or 0)*100) if (a.get(479,0) and a.get(681,0)) else 0"
    RATIOS[
        'Leverage'] = "(float(a.get(519) or 0) / float(a.get(681) or 0)) if (a.get(519,0) and a.get(681,0)) else 0"
    RATIOS[
        'Corriente'] = "(float(a.get(668) or 0) / float(a.get(519) or 0)*100) if (a.get(668,0) and a.get(519,0)) else 0"
    RATIOS[
        'No Corriente'] = "(float(a[809] or 0) / float(a[519] or 0)*100) if (a.get(809,0) and a.get(519,0)) else 0"
    RATIOS[
        'Margen Neto'] = "(float(a.get(479) or 0) / float(a.get(540) or 0)*100) if (a.get(479,0) and a.get(540,0)) else 0"
    RATIOS[
        'Rotacion Activos'] = "(float(a.get(540) or 0) / float(a.get(808) or 0)) if (a.get(540,0) and a.get(808,0)) else 0"
    RATIOS[
        'Apalancamiento'] = "(float(a.get(808) or 0) / float(a.get(681) or 0)) if (a.get(808,0) and a.get(681,0)) else 0"
    RATIOS[
        'Dupont'] = "(((float(a.get(479) or 0) / float(a.get(540) or 0)) * (float(a.get(540) or 0) / float(a.get(808) or 0))) * (float(a.get(808) or 0) / float(a.get(681) or 0))*100)  if (a.get(479,0) and a.get(540,0)and a.get(808,0)and a.get(681,0)) else 0"
    RATIOS[
        'BPA'] = "(float(a.get(479) or 0) / float(a.get(685) or 0)) if (a.get(479,0) and a.get(685,0)) else 0"
    RATIOS[
        'Dias de Caja'] = "((float(a.get(739) or 0) / (float(a.get(540) or 1) - float(a.get(479)))) * 365) if (a.get(739,0) and a.get(540,0) and a.get(479)) else 0"
    RATIOS[
        'Ebitda'] = "(float(a.get(479) or 0) + float(a.get(764)or 0) + float(a.get(476)or 0) + float(a.get(864)or 0)) if (a.get(479,0) and a.get(764,0) and a.get(476) and a.get(864)) else 0"
    RATIOS[
        'Cobertura Interes'] = "((float(a.get(479) or 0) + float(a.get(764)) + float(a.get(476)) + float(a.get(832)) + float(a.get(865)))) / float(a.get(764) or 0) if (a.get(479,0) and a.get(764,0) and a.get(476) and a.get(832) and a.get(865)) else 0"
    RATIOS[
        'Rotacion De Inventarios'] = "(float(a.get(695) or 0) / float(a.get(727) or 0)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'Tasa Interes Promedio'] = "float(a.get(764) or 0) / (((float(a.get(582) or 0) + float(a.get(791) or 0) + float(b.get(582) or 0)+ float(b.get(791) or 0)))/2) if (a.get(764,0) and a.get(582,0)and a.get(791,0)  and b.get(582,0)and b.get(791,0)) else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_ratiosindustria  where cod_industria = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    cod_entidad,desc_entidad from entidad where cod_industria ='%s' order by cod_entidad""" % (
            cod_entidad))
    entidad = cursor.fetchall()
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_ratiosindustria  where cod_industria = '%s' and anio in ('%s') and mes in ('%s') order by cod_entidad"""
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["RATIOS"]
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:

            COLUMNAS.insert(1, resumen[0][2])
            b = dict()
            a = dict()
            ant = []
            rest = dict()
            RESULTADO = {}
            for e in entidad:
                if ant:
                    if ant[0] != e[0] and ant != None:
                        a = dict()
                        rest[ant[0]] = RESULTADO
                        RESULTADO = {}
                for r in resumen:
                    a[r[5]] = r[10]
                for r in RATIOS:
                    raux = RESULTADO.get(r, [r])
                    raux.insert(1, eval(RATIOS[r]))
                    RESULTADO[r] = raux
                ant = e
                b=a
            rest[ant[0]] = RESULTADO
    return rest, COLUMNAS


@app.route('/roles', methods=["GET", "POST"])
def roles():
    if session["username"] != 'unknown':
        cur = cnx.cursor()
        cur.execute("select * from role")
        data = cur.fetchall()
        return render_template("/roles.html", dato=data)
    return redirect("login")


@app.route('/roleCuenta/<cod_role>', methods=["GET", "POST"])
def rolesCuenta(cod_role):
    if session["username"] != 'unknown':
        cur = cnx.cursor()
        cur.execute("select * from cuenta join role_cuenta using (cod_cuenta) where cod_role ='%s'" % cod_role)
        data = cur.fetchall()
        return render_template("/roleCuenta.html", dato=data)
    return redirect("login")


@app.route('/reportes/<cod_documento>/<cod_role>', methods=["GET", "POST"])
def reportes(cod_documento, cod_role):
    if session["username"] != 'unknown':
        sql = cnx.cursor()
        sql.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, case when not decimales isnull then desc_detalle_documento::numeric / 10 ^ abs(decimales) else 0 end valor 
                    from detalle_documento 
                    join cuenta using (cod_cuenta) 
                    left join role_cuenta using (cod_cuenta)
                    left join role using(cod_role)
                    left join unidad using (cod_unidad)
                    join tipo_cuenta using (cod_tipo_cuenta)
                    join contexto using (cod_contexto) 
                    join entidad using (cod_entidad)
                    join periodo using (cod_periodo) 
                    left join context_escenarios using (cod_contexto) 
                    left join escenario using (cod_escenario) 
                    left join dimension using (cod_dimension) 
                    --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
                    where cod_dimension is null  and cod_documento = %s and cod_role =%s
                    order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role))
        data = sql.fetchall()
        if data[0] == []:
            flash("No Existe")
            return render_template("/detalle_documento")
        for d in data:
            desc_role = d[0]
            entidad = d[13]
            cuenta = d[5]
            dineros = d[8]
            fechas = d[7]
        return render_template("/reportes.html", data=data, desc_role=desc_role, entidad=entidad, cuenta=cuenta,
                               dineros=dineros, fechas=fechas)
    return redirect("login")


@app.route('/pdf/<cod_documento>/<cod_role>', methods=["GET", "POST"])
def pdf(cod_documento, cod_role):
    cursor = cnx.cursor()
    cursor.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, case when not decimales isnull then desc_detalle_documento::numeric / 10 ^ abs(decimales) else 0 end valor 
                            from detalle_documento 
                            join cuenta using (cod_cuenta) 
                            left join role_cuenta using (cod_cuenta)
                            left join role using(cod_role)
                            left join unidad using (cod_unidad)
                            join tipo_cuenta using (cod_tipo_cuenta)
                            join contexto using (cod_contexto) 
                            join entidad using (cod_entidad)
                            join periodo using (cod_periodo) 
                            left join context_escenarios using (cod_contexto) 
                            left join escenario using (cod_escenario) 
                            left join dimension using (cod_dimension) 
                            --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
                            where cod_dimension is null  and cod_documento = %s and cod_role =%s
                            order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role))
    data = dictfetchall(cursor)
    cursor.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, case when not decimales isnull then desc_detalle_documento::numeric / 10 ^ abs(decimales) else 0 end valor 
                                from detalle_documento 
                                join cuenta using (cod_cuenta) 
                                left join role_cuenta using (cod_cuenta)
                                left join role using(cod_role)
                                left join unidad using (cod_unidad)
                                join tipo_cuenta using (cod_tipo_cuenta)
                                join contexto using (cod_contexto) 
                                join entidad using (cod_entidad)
                                join periodo using (cod_periodo) 
                                left join context_escenarios using (cod_contexto) 
                                left join escenario using (cod_escenario) 
                                left join dimension using (cod_dimension) 
                                --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
                                where cod_dimension is null  and cod_documento = %s and cod_role =%s
                                order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role))
    date = cursor.fetchall()
    cursor.execute("""select distinct desc_periodo 
                               from detalle_documento 
                               join cuenta using (cod_cuenta) 
                               left join role_cuenta using (cod_cuenta)
                               left join role using(cod_role)
                               join contexto using (cod_contexto) 
                               join periodo using (cod_periodo)
                               left join context_escenarios using (cod_contexto) 
                               left join escenario using (cod_escenario) 
                               left join dimension using (cod_dimension)
                               where cod_dimension is null  and cod_documento = %s and cod_role =%s
                               order by desc_periodo desc""" % (cod_documento, cod_role))
    per = dictfetchall(cursor)
    for d in date:
        cod_rol = d[1]
        desc_role = d[0]
        entidad = d[13]
        cuenta = d[5]
    hoy = datetime.now()
    hoy = hoy.strftime("%Y-%m-%d")
    report = PdfCustomDetail(filename="%s.pdf" % (cod_rol), title=["%s" % (desc_role), entidad.__str__(), cuenta],
                             logo=getattr(sys, 'logo', 'xeeffy_logo_index.png'))
    pvt_kms = pivot(data, ('cod_role_cuenta', 'desc_cuenta'), ('desc_periodo',), 'valor')
    datas = []
    columnas = ["CUENTA"]
    data_linea = ['']
    ancho_total = 0
    colsWidth = [0]
    colAlign = ['LEFT']
    colType = ['str']
    for p in per:
        columnas.append(p['desc_periodo'])
        data_linea.append(0.0)
        colsWidth.append(60)
        ancho_total += 60
        colAlign.append("RIGHT")
        colType.append("str")
    colsWidth[0] = 540 - ancho_total
    for f in pvt_kms:
        dl = list(f.get(('cod_role_cuenta', 'desc_cuenta'), ['']))
        for p in per:
            dl.append(f.get((p['desc_periodo'],), 0))
        datas.append(dl)
    data_final = []
    datas.sort()
    for d in datas:
        data_final.append(d[1:])
    return render_template("/pdf.html", d=data_final, columnas=columnas, entidad=entidad, desc_role=desc_role, hoy=hoy)


def __build_dict(description, row):
    res = {}
    for i in range(len(description)):
        res[description[i][0]] = row[i]
    return res


def dictfetchall(cursor):
    res = []
    rows = cursor.fetchall()
    for row in rows:
        res.append(__build_dict(cursor.description, row))
    return res


class PdfCustomDetail:
    def __init__(self, title="Documento Generico", filename="output.pdf", barcode=None, companyInfo=[], logo=None,
                 distintoEncabezado=True):
        self.Elements = []
        self.Data = []
        self.Headers = []
        self.logo = logo
        self.filename = filename.replace(" ", "_")
        self.distintoEncabezado = distintoEncabezado
        self.styleSheet = getSampleStyleSheet()
        self.Title = title
        self.Author = "XSolution ERP"
        self.URL = "http://www.xsolution.cl"
        if companyInfo == []:
            self.CompanyInfo = [["Empresa.", 0],
                                ["RUT: 99.000.000-0", 1],
                                ["Direccion", 2],
                                ["Fonos", 3]]
        else:
            self.CompanyInfo = companyInfo
        self.email = "contacto@xsolution.cl"
        self.pageinfo = "%s / %s / %s" % (self.Author, self.email, self.Title)
        self.barcode = barcode


@app.route('/importCMF', methods=["GET", "POST"])
def importCMF():
    if session["username"] != 'unknown':
        if request.method == "POST":
            import urllib.request
            import urllib

            cur = cnx.cursor()
            ano = request.form["ano"]
            mes = request.form["mes"]
            mes = mes.zfill(2)
            url = r"http://www.cmfchile.cl/institucional/mercados/novedades_envio_sa_ifrs_excel2.php?aa=%s&mm=%s" % (
                ano, mes)
            filename = "%s%s%s_%s%s.xls" % (
                tempfile._get_default_tempdir(), os.sep, tempfile._RandomNameSequence().__next__(), ano, mes)
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent',
                                  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
            user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
            values = {'name': 'Michael Foord',
                      'location': 'Northampton',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            urllib.request.install_opener(opener)
            data1 = urllib.request.urlretrieve(url, filename)
            http = urllib3.PoolManager()
            response = http.request('GET', url)
            soup = BeautifulSoup(response.data)
            book = xlrd.open_workbook(filename)
            sh = book.sheet_by_index(0)
            for rx in range(4, sh.nrows, 1):
                fpenvio = sh.cell(rx, 0).value
                fuenvio = sh.cell(rx, 1).value
                razon_social = sh.cell(rx, 2).value
                tipo_balance = sh.cell(rx, 3).value
                rut, dv = sh.cell(rx, 4).value.split("-")
                cur.execute("""
                SELECT
                public.entidad.cod_entidad,
                public.entidad.desc_entidad,
                public.entidad.user_id
                FROM
                public.entidad
                WHERE entidad.cod_entidad = '%s'""" % (CRut("%s-%s" % (rut, dv))))
                dato = cur.fetchall()
                if not dato:
                    flash("No existe")
                    cur.execute("""INSERT INTO entidad(cod_entidad,desc_entidad)
                    VALUES('%s','%s')""" % (CRut("%s-%s" % (rut, dv)), razon_social))
                    cnx.commit()
                tipo_envio = sh.cell(rx, 5).value
                filtros = {'rut': rut, 'mes': mes, 'anio': ano, 'archivo': "Estados%20financieros%20(XBRL)",
                           'tipo': tipo_balance.upper()[0]}
                desc_doc = "%(rut)s_%(anio)s%(mes)s_%(tipo)s.zip" % (filtros)
                cur.execute("""SELECT
                public.documento.cod_documento,
                public.documento.desc_documento,
                public.documento.cod_entidad,
                public.entidad.desc_entidad,
                public.documento.anio,
                public.documento.mes
                FROM
                public.documento,
                public.entidad
                WHERE documento.cod_entidad='%s' and documento.desc_documento ='%s' and entidad.desc_entidad = '%s' and documento.anio='%s' and documento.mes ='%s'""" % (
                    CRut("%s-%s" % (rut, dv)), desc_doc, razon_social, ano, mes))
                doc = cur.fetchall()
                if not doc:
                    print("NUEVO!!!", desc_doc, rx, "de", sh.nrows)
                    has = "*"
                    cur.execute(
                        """INSERT INTO documento(desc_documento,cod_entidad,anio,mes,hash)VALUES('%s','%s','%s','%s','%s')""" % (
                            desc_doc, CRut("%s-%s" % (rut, dv)), ano, mes, has))

                    url_zip = "http://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs/safec_ifrs_verarchivo.php?auth=&send=&rut=%(rut)s&mm=%(mes)s&aa=%(anio)s&archivo=%(rut)s_%(anio)s%(mes)s_%(tipo)s.zip&desc_archivo=%(archivo)s&tipo_archivo=XBRL" % (
                        filtros)
                    filename_zip = tempfile._get_default_tempdir() + os.sep + tempfile._RandomNameSequence().__next__() + "%(rut)s_%(anio)s%(mes)s_C.zip" % (
                        filtros)
                    try:
                        values = {'name': 'Michael Foord',
                                  'location': 'Northampton',
                                  'language': 'Python'}
                        data1 = urllib.parse.urlencode(values).encode("utf-8")
                        req = urllib.request.Request(url_zip, data1, headers)
                        with urllib.request.urlopen(req, data=data1) as f:
                            resp = f.read()
                        f = open(filename_zip, "wb")
                        f.write(resp)
                        f.close()
                        input_zip = zipfile.ZipFile(filename_zip)
                        data = {name: input_zip.read(name) for name in input_zip.namelist() if
                                name.upper().endswith('.XBRL')}
                        for arch in data.keys():
                            # jxbrl = jsobXBrl(cod_documento=doc.get_cod_documento())
                            cursor = cnx.cursor()
                            cursor.execute("SELECT currval('documento_cod_documento_seq')")
                            jxbrl = jsobXBrl(cod_documento=cursor.fetchone()[0])
                            jxbrl.loadXBrlFromMenory(data.get(arch))
                            jxbrl.processJsonXbrl()
                            print("hola")
                        #     del jxbrl
                        # del data
                        cnx.commit()
                    except:
                        print("ERROR", desc_doc, sys.exc_info()[1])
                else:
                    print("EXISTE!!!", desc_doc, rx, "de", sh.nrows)
                del doc
            return redirect("/documentos")
        return render_template("/importCMF.html")
    return redirect("/login")


class jsobXBrl():
    def __init__(self, xbrlFile=None, cod_documento=None):
        self.cod_documento = cod_documento
        self.xbrlFile = xbrlFile
        self.jsonXBrl = None
        self.contexts = {}
        self.data = []
        self.entity = {}
        self.period = {}
        self.scenario = {}
        self.tipo_scenario = {}
        self.dimension = {}
        self.tipoCuenta = {}
        self.cuentas = {}
        self.unidades = {}
        self.loadUnidades()
        self.loadTipoCuenta()
        self.loadCuentas()
        self.loadEntity()
        self.loadPeriod()
        self.loadDimension()
        self.loadTipoScenario()

        pass

    def processJsonXbrl(self):
        for i in self.jsonXBrl:
            if i.split(":")[-1] == 'context':
                for c in self.jsonXBrl.get(i):
                    self.addContext(c)
            elif i.split(":")[-1] == 'unit':
                for u in self.jsonXBrl.get(i):
                    self.addUnit(u)
            else:
                pass
        for i in self.jsonXBrl:
            if i == 'context':
                pass
            elif i == 'unit':
                pass
            else:
                self.addData(i, self.jsonXBrl.get(i))
        print("OK")

    def addCuenta(self, data):
        # from orm.common_services.public.cms_cuenta import cms_cuenta
        # from orm.common_services.public.cms_tipo_cuenta import cms_tipo_cuenta
        tc, cta = data.split(":")
        ccta = self.cuentas.get(":".join([{'ifrs': "ifrs-full"}.get(tc, tc), cta]))

        if ccta:
            return ccta
        if not self.tipoCuenta.get(tc):
            cursor = cnx.cursor()
            cursor.execute("insert into tipo_cuenta(desc_tipo_cuenta) values ('%s')" % (tc))
            # tcta = cms_tipo_cuenta()
            # tcta.set_desc_tipo_cuenta(tc)
            cnx.commit()
            # tcta.save()
            cursor.execute("SELECT currval('tipo_cuenta_cod_tipo_cuenta_seq')")
            # ctc = tcta.get_cod_tipo_cuenta()
            self.tipoCuenta[tc] = cursor.fetchone()[0]
        else:
            ctc = self.tipoCuenta.get(tc)
        cursor = cnx.cursor()
        cursor.execute("insert into cuenta(cod_tipo_cuenta,desc_cuenta) values ('%s','%s')" % (ctc, cta))
        cnx.commit()
        cursor.execute("SELECT currval('cuenta_cod_cuenta_seq')")
        # objcta = cms_cuenta()
        # objcta.set_desc_cuenta(cta)
        # objcta.set_cod_tipo_cuenta(ctc)
        # objcta.save()
        # ccta = objcta.get_cod_cuenta()
        ccta = cursor.fetchone()[0]
        self.cuentas[data] = ccta
        return ccta

    def loadTipoCuenta(self):
        # from orm.common_services.public.cms_tipo_cuenta import cms_tipo_cuenta
        # tc = cms_tipo_cuenta()
        cursor = cnx.cursor()
        cursor.execute("select cod_tipo_cuenta, desc_tipo_cuenta from tipo_cuenta")
        for t in cursor.fetchall():
            # self.tipoCuenta[t.get_desc_tipo_cuenta()] = t.get_cod_tipo_cuenta()
            self.tipoCuenta[t[1]] = t[0]

    def loadCuentas(self):
        # from orm.common_services.public.cms_cuenta import cms_cuenta
        # cs = cms_cuenta()
        cursor = cnx.cursor()
        cursor.execute("""SELECT
        public.tipo_cuenta.desc_tipo_cuenta,
        public.cuenta.desc_cuenta,
        public.cuenta.cod_cuenta,
        public.cuenta.cod_tipo_cuenta
        FROM
        public.cuenta
        INNER JOIN public.tipo_cuenta ON public.cuenta.cod_tipo_cuenta = public.tipo_cuenta.cod_tipo_cuenta""")
        # for c in cs.custom_query(
        # "select desc_tipo_cuenta||':'||desc_cuenta, cod_cuenta from cuenta join tipo_cuenta using (cod_tipo_cuenta)"):
        for c in cursor.fetchall():
            self.cuentas[c[0]] = c[1]

    def addData(self, t, data):
        try:
            cursor = cnx.cursor()
            cta = self.cuentas.get(t)
            if not cta:
                cta = self.addCuenta(t)

            if isinstance(data, dict):
                c = self.contexts.get(data.get("@contextRef"), {}).get('id')
                d = data.get('@decimals')
                u = self.unidades.get(data.get('@unitRef'))
                valor = data.get("#text")
                cursor.execute(
                    """insert into detalle_documento (cod_documento, cod_cuenta, cod_contexto ,decimales, cod_unidad,desc_detalle_documento)values('%s','%s','%s','%s','%s','%s')""" % (
                        self.cod_documento, cta, c, d, u, valor))
                # dd = cms_detalle_documento()
                # dd.set_cod_documento(self.cod_documento)
                # dd.set_cod_cuenta(cta)
                # dd.set_cod_contexto(c)
                # dd.set_decimales(d)
                # dd.set_cod_unidad(u)
                # dd.set_desc_detalle_documento(valor)
                # dd.save()
                cnx.commit()
                self.data.append([cta, c, d, u, valor])
            elif isinstance(data, list):
                for i in data:
                    c = self.contexts.get(i.get("@contextRef"), {}).get('id')
                    d = i.get('@decimals')
                    u = self.unidades.get(i.get('@unitRef'))
                    valor = i.get("#text")
                    cursor.execute(
                        """insert into detalle_documento (cod_documento, cod_cuenta, cod_contexto ,decimales, cod_unidad,desc_detalle_documento)values('%s','%s','%s','%s','%s','%s')""" % (
                            self.cod_documento, cta, c, d, u, valor))
                    # dd = cms_detalle_documento()
                    # dd.set_cod_documento(self.cod_documento)
                    # dd.set_cod_cuenta(cta)
                    # dd.set_cod_contexto(c)
                    # dd.set_decimales(d)
                    # dd.set_cod_unidad(u)
                    # dd.set_desc_detalle_documento(valor)
                    # dd.save()
                    cnx.commit()
                    self.data.append([cta, c, d, u, valor])
            else:
                print(t, data)
        except:
            print(t, data)
        # print len(self.data)

    def loadUnidades(self):
        # from orm.common_services.public.cms_unidad import cms_unidad
        cursor = cnx.cursor()
        cursor.execute("select cod_unidad,desc_unidad from unidad")
        for u in cursor.fetchall():
            # self.unidades[u.get_desc_unidad()] = u.get_cod_unidad()
            self.unidades[u[1]] = u[0]

    def addUnit(self, data):
        cursor = cnx.cursor()
        # from orm.common_services.public.cms_unidad import cms_unidad
        if self.unidades.get(data.get("@id")):
            return
        # uni = cms_unidad()
        # uni.set_desc_unidad(data.get("@id"))
        # uni.save()
        cursor.execute("insert into unidad(desc_unidad)values ('%s')" % (data.get("@id")))
        cnx.commit()
        # cursor.execute("select cod_unidad from unidad where desc_unidad ='%s'"% (data.get("@id")))
        # uni = cursor.fetchall()
        cursor.execute("SELECT currval('unidad_cod_unidad_seq')")
        self.unidades[data.get("@id")] = cursor.fetchone()[0]
        print(data)

    def addDimension(self, data):
        cod = self.dimension.get(data.get('@dimension'))
        if not cod:
            # from orm.common_services.public.cms_dimension import cms_dimension
            cursor = cnx.cursor()
            cursor.execute("insert into dimension(desc_dimension)values('%s')" % (data.get('@dimension')))
            cnx.commit()
            # cursor.execute("select cod_dimension from dimension where desc_dimension = '%s'" % (data.get('@dimension')))
            # cod = cursor.fetchall()
            cursor.execute("SELECT currval('dimension_cod_dimension_seq')")
            # obj = cms_dimension()
            # obj.set_desc_dimension(data.get('@dimension'))
            # obj.save()
            # cod = obj.get_cod_dimension()
            self.dimension[data.get('@dimension')] = cursor.fetchone()[0]
        return cod

    def loadDimension(self):
        # from orm.common_services.public.cms_dimension import cms_dimension
        # obj = cms_dimension()
        cursor = cnx.cursor()
        cursor.execute("select cod_dimension , desc_dimension from dimension")
        for obj in cursor.fetchall():
            # self.dimension[obj.get_desc_dimension()] = obj.get_cod_dimension()
            self.dimension[obj[1]] = obj[0]

    def loadScenario(self):
        # from orm.common_services.public.cms_escenario import cms_escenario
        cursor = cnx.cursor()
        cursor.execute("""SELECT
        public.escenario.desc_escenario,
        public.tipo_escenario.desc_tipo_escenario,
        public.dimension.desc_dimension,
        public.escenario.cod_escenario
        FROM
        public.escenario
        INNER JOIN public.tipo_escenario ON public.escenario.cod_tipo_escenario = public.tipo_escenario.cod_tipo_escenario
        INNER JOIN public.dimension ON public.escenario.cod_dimension = public.dimension.cod_dimension""")
        # es = cms_escenario()
        for es in cursor.fetchall():
            # self.scenario[(es.get_desc_escenario(), es.get_tipo_escenario().__str__(),
            #                es.get_dimension().__str__())] = es.get_cod_escenario()
            self.scenario[es[0], es[1], es[2]] = es[3]

    def addScenario(self, data):
        cods = []
        if data:
            for key in data.keys():
                if isinstance(data.get(key), dict):
                    escenarios = [data.get(key)]
                else:
                    escenarios = data.get(key)
                for escenario in escenarios:
                    cod = self.scenario.get((escenario.get('#text'), key, escenario.get('@dimension')))
                    if not cod:
                        cursor = cnx.cursor()
                        ts = self.addTipoScenario(key)
                        d = self.addDimension(escenario)
                        # from orm.common_services.public.cms_escenario import cms_escenario
                        cursor.execute(
                            "insert into escenario(desc_escenario,cod_dimension,cod_tipo_escenario)values('%s','%s','%s')" % (
                                escenario.get('#text'), d, ts))
                        cursor.execute("SELECT currval('escenario_cod_escenario_seq')")
                        cnx.commit()
                        cod = cursor.fetchone()[0]
                        self.scenario[(escenario.get('#text'), key, escenario.get('@dimension'))] = cod
                    cods.append(cod)
        return cods

    def addTipoScenario(self, key):
        cod = self.tipo_scenario.get(key)
        if not cod:
            # from orm.common_services.public.cms_tipo_escenario import cms_tipo_escenario as clas
            cursor = cnx.cursor()
            cursor.execute("insert into tipo_escenario(desc_tipo escenario)values('%s')" % (key))
            cnx.commit()
            # obj = clas()
            # obj.set_desc_tipo_escenario(key)
            # obj.save()
            cursor.execute("SELECT currval('tipo_escenario_cod_tipo_escenario_seq')")
            # cursor.execute("select cod_tipo_escenario from tipo_escenario where desc_tipo_escenario='%s'" % (key))
            # cod = obj.get_cod_tipo_escenario()
            # cod = cursor.fetchall()
            self.tipo_scenario[key] = cursor.fetchone()[0]
        return cod

    def loadTipoScenario(self):
        # from orm.common_services.public.cms_tipo_escenario import cms_tipo_escenario as clas
        # obj = clas()
        cursor = cnx.cursor()
        cursor.execute("select cod_tipo_escenario,desc_tipo_escenario from tipo_escenario")
        for obj in cursor.fetchall():
            # self.tipo_scenario[obj.get_desc_tipo_escenario()] = obj.get_cod_tipo_escenario()
            self.tipo_scenario[obj[1]] = obj[0]

    def loadXBrlFromFile(self):
        md5 = self.hash_bytestr_iter(self.file_as_blockiter(open(self.xbrlFile, 'rb')), hashlib.sha256(), True)
        fxml = open(self.xbrlFile)
        xml = fxml.read()
        xml = eval(xmltodict.parse(xml))
        self.jsonXBrl = None
        keys = ['xbrli:xbrl', 'xbrl']
        for key in keys:
            self.jsonXBrl = xml.get(key)
            if self.jsonXBrl:
                return
        print("No Encontro XBRL")

    def hash_bytestr_iter(self, bytesiter, hasher, ashexstr=False):
        for block in bytesiter:
            hasher.update(block)
        return (hasher.hexdigest() if ashexstr else hasher.digest())

    def file_as_blockiter(self, afile, blocksize=65536):
        with afile:
            block = afile.read(blocksize)
            while len(block) > 0:
                yield block
                block = afile.read(blocksize)

    def loadEntity(self):
        # from orm.common_services.public.cms_entidad import cms_entidad
        cursor = cnx.cursor()
        cursor.execute("select cod_entidad from entidad")
        for e in cursor.fetchall():
            # self.entity[e.get_cod_entidad()] = e.get_cod_entidad()
            self.entity[e[0]] = e[0]

    def addEntity(self, data):
        cod = self.entity.get(CRut(data.get('identifier', data.get('xbrli:identifier')).get('#text')))
        cod1 = cod
        if not cod:
            cursor = cnx.cursor()
            # from orm.common_services.public.cms_entidad import cms_entidad
            cursor.execute("insert into entidad (cod_entidad, desc_entidad) values ('%s','%s')" % (
                CRut(data.get('identifier', data.get('xbrli:identifier')).get('#text')),
                data.get('identifier', data.get('xbrli:identifier')).get('#text')))
            cnx.commit()
            # enty = cms_entidad()
            # enty.set_cod_entidad((CRut(data.get('identifier', data.get('xbrli:identifier')).get('#text'))))
            # enty.set_desc_entidad(data.get('identifier', data.get('xbrli:identifier')).get('#text'))
            # enty.save()
            cursor.execute("select cod_entidad from entidad where cod_entidad ='%s' and desc_entidad ='%s'" % (
                (CRut(data.get('identifier', data.get('xbrli:identifier')).get('#text')))),
                           data.get('identifier', data.get('xbrli:identifier')).get('#text'))
            cod = cursor.fetchall()
            # cod = enty.get_cod_entidad()
            # self.entity[enty.get_cod_entidad()] = cod
            self.entity[CRut(data.get('identifier', data.get('xbrli:identifier')).get('#text'))] = cod[0][0]
        return cod

    def addContext(self, data):
        cursor = cnx.cursor()
        if [k for k in data.keys() if not k.split(":")[-1] in ("entity", 'period', 'scenario', '@id')]:
            print(data)
        if self.contexts.get(data['@id']):
            return
        e = self.addEntity(data.get("entity", data.get("xbrli:entity")))
        self.addPeriod(data.get('period', data.get('xbrli:period')))
        p = self.getPeriod(data.get('period', data.get('xbrli:period')))
        scenarios = self.addScenario(data.get('scenario', data.get('xbrli:scenario')))
        # scenarios = self.getScenario(data.get('scenario',data.get('xbrli:scenario')))
        # from orm.common_services.public.cms_contexto import cms_contexto
        # c = cms_contexto()
        # c.set_cod_entidad(e)
        # c.set_cod_periodo(p)
        # # c.set_cod_escenario(s)
        # c.set_desc_contexto(data['@id'])
        # c.save()
        cursor.execute(
            "insert into contexto(cod_entidad, cod_periodo, desc_contexto) values ('%s','%s','%s')" % (
                e, p, data['@id']))
        cnx.commit()
        cursor.execute("SELECT currval('contexto_cod_contexto_seq')")
        codigo_contexto = cursor.fetchone()[0]
        self.contexts[data['@id']] = {"entity": e, "period": p, "id": codigo_contexto}
        # from orm.common_services.public.cms_context_escenarios import cms_context_escenarios
        for s in scenarios:
            cursor.execute(
                "insert into context_escenarios(cod_contexto,cod_escenario,desc_context_escenarios) values('%s','%s','.')" % (
                    codigo_contexto, s))
            # ce = cms_context_escenarios()
            # ce.set_cod_contexto(c.get_cod_contexto())
            # ce.set_cod_escenario(s)
            # ce.set_desc_context_escenarios(".")
            # ce.save()
            cnx.commit()

    def getScenario(self, data):
        if data:
            for key in data.keys():
                return self.scenario[(data.get(key).get('#text'), key, data.get(key).get('@dimension'))]

        # def getScenario(self, data):
        #     if data:
        #         for key in data.keys():
        #             return self.scenario[(data.get(key).get('#text'), key, data.get(key).get('@dimension'))]
        # cursor.execute("select cod_contexto from contexto where cod_entidad='%s'and cod_periodo='%s' and desc_contexto = '%s'"%(e, p, data['@id']))
        # a = cursor.fetchall()
        # self.contexts[data['@id']] = {"entity": e, "period": p, "id": a}
        # self.contexts[data['@id']] = {"entity": e, "period": p, "id": c.get_cod_contexto()}
        # from orm.common_services.public.cms_context_escenarios import cms_context_escenarios
        # for s in scenarios:
        #     cursor.execute = (
        #             "insert into context_excenarios(cod_contexto,cod_escenario,desc_context_escenario) values ('%s','%s','%s')" % (a, s, "."))
        #     f = cursor.fetchall()
        #     cnx.commit()
        # ce = cms_context_escenarios()
        # ce.set_cod_contexto(c.get_cod_contexto())
        # ce.set_cod_escenario(s)
        # ce.set_desc_context_escenarios(".")
        # ce.save()

    def getPeriod(self, data):
        return self.period.get((data.get('startDate', data.get('xbrli:startDate')),
                                data.get('endDate', data.get('xbrli:endDate')),
                                data.get("instant", data.get("xbrli:instant"))))

    def addPeriod(self, data):
        cursor = cnx.cursor()
        if not self.period.get((data.get('startDate', data.get('xbrli:startDate')),
                                data.get('endDate', data.get('xbrli:endDate')),
                                data.get("instant", data.get("xbrli:instant")))):
            # from orm.common_services.public.cms_periodo import cms_periodo
            sql = "insert into periodo(desc_periodo,"
            valores = "('.',"
            for d in data:
                if data[d]:
                    sql += d.replace('xbrli:', '') + ","
                    valores += "'" + data[d] + "',"
            sql = sql[:-1] + ") values " + valores[:-1] + ")"
            cursor.execute(sql)
            # if data.get("xbrli:instant"):
            #     cursor.execute("insert into periodo (startdate,enddate,instant,desc_periodo)values ('%s','%s','%s','.')"%(data.get('startDate', data.get('xbrli:startDate')),data.get('endDate', data.get('xbrli:endDate')),data.get('instant', data.get('xbrli:instant'))or 'Null'))
            # else:
            #     cursor.execute("insert into periodo (startdate,enddate,desc_periodo)values ('%s','%s','.')" % (
            #     data.get('startDate', data.get('xbrli:startDate')), data.get('endDate', data.get('xbrli:endDate'))
            #     ))

            cnx.commit()
            cursor.execute("SELECT currval ('periodo_cod_periodo_seq')")
            self.period[(
                data.get('startDate', data.get('xbrli:startDate')), data.get('endDate', data.get('xbrli:endDate')),
                data.get("instant", data.get("xbrli:instant")))] = cursor.fetchone()[0]
            # p = cms_periodo()
            # p.set_startdate(data.get('startDate', data.get('xbrli:startDate')))
            # p.set_enddate(data.get('endDate', data.get('xbrli:endDate')))
            # p.set_instant(data.get('instant', data.get('xbrli:instant')))
            # p.set_desc_periodo(".")
            # p._pre_save()
            # p.save()
            # self.period[(
            #     data.get('startDate', data.get('xbrli:startDate')), data.get('endDate', data.get('xbrli:endDate')),
            #     data.get("instant", data.get("xbrli:instant")))] = p.get_cod_periodo()

    def loadPeriod(self):
        # from orm.common_services.public.cms_periodo import cms_periodo
        cursor = cnx.cursor()
        cursor.execute("select cod_periodo, startdate, enddate,instant from periodo")
        # per = cms_periodo()
        for p in cursor.fetchall():
            # s = p.get_startdate().__str__() if p.get_startdate() else None
            # e = p.get_enddate().__str__() if p.get_enddate() else None
            # i = p.get_instant().__str__() if p.get_instant() else None
            self.period[(p[1], p[2], p[3])] = p[0]

    def loadXBrlFromMenory(self, dataXML):

        soup = BeautifulSoup(dataXML, 'lxml')
        btree = BeautifulSoup(dataXML, 'lxml')
        Terms = btree.select('xbrli > xbrli')
        jsonObj = {"xbrli": []}
        for term in Terms:
            termDetail = {
                "xbrli:xbrl": term.find('xbrli:xbrl').text,
                "xbrl": term.find('xbrl').text
            }
            RelatedTerms = term.select('RelatedTerms > Term')
            if RelatedTerms:
                termDetail["RelatedTerms"] = []
                for rterm in RelatedTerms:
                    termDetail["RelatedTerms"].append({
                        "Title": rterm.find('Title').text,
                        "Relationship": rterm.find('Relationship').text
                    })
            jsonObj["thesaurus"].append(termDetail)
        tag_list = soup.find_all()
        for tag in tag_list:
            if tag.name == 'us-gaap:liabilities':
                print('Liabilities: ' + tag.text)
        import json
        import xmltodict
        # xml = eval(xmljson(dataXML).replace("null", "None"))
        jsonString = xmltodict.parse(dataXML)

        self.jsonXBrl = None
        keys = ['xbrli:xbrl', 'xbrl']
        for key in keys:
            self.jsonXBrl = jsonString.get(key)
            if self.jsonXBrl:
                return
        print("No Encontro XBRL")

    def loadContext(self):
        # from orm.common_services.public.cms_contexto import cms_contexto
        # c = cms_contexto()
        cursor = cnx.cursor()
        cursor.execute("select cod_contexto,cod_entidad,cod_periodo,desc_contexto from cotexto")
        for c in cursor.fetchall():
            # self.contexts[c.get_desc_contexto()] = {"entity": c.get_cod_entidad(), "period": c.get_cod_periodo(),
            #                                         "id": c.get_cod_contexto()}
            self.contexts[c[3]] = {"entity": c[1], "period": c[2], "id": c[0]}


def get_eresultado(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades ordinarias'] = "(float(a.get(540,1)))  if  (a.get(540,0))  else 0"
    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)))  if  a.get(727,0)  else 0"
    RATIOS[
        'Ganancias Bruta'] = "(float(a.get(805,1)))  if  a.get(805,0)  else 0"
    RATIOS[
        'Otros Ingresos'] = "(float(a.get(682,1)))  if  a.get(682,0)  else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,1)))  if  a.get(1324,0)  else 0"
    RATIOS[
        'Gastos de administración'] = "(float(a.get(618,1)))  if  a.get(618,0)  else 0"
    RATIOS[
        'Otros gastos, por función'] = "(float(a.get(1325,1)))  if  a.get(1325,0)  else 0"
    RATIOS[
        'Otras ganancias (pérdidas)'] = "(float(a.get(815,1)))  if  a.get(815,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) de actividades operacionales'] = "(float(a.get(817,1)))  if  a.get(817,0)  else 0"
    RATIOS[
        'Ingresos financieros'] = "(float(a.get(558,1)))  if  a.get(558,0)  else 0"
    RATIOS[
        'Costos financieros'] = "(float(a.get(764,1)))  if  a.get(764,0)  else 0"
    RATIOS[
        'Participación en las ganancias (pérdidas) de asociadas y negocios'] = "(float(a.get(824,1)))  if  a.get(824,0)  else 0"
    RATIOS[
        'Diferencias de cambio'] = "(float(a.get(849,1)))  if  a.get(849,0)  else 0"
    RATIOS[
        'Resultados por unidades de reajuste'] = "(float(a.get(516,1)))  if  a.get(516,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) que surgen de diferencias entre importes en libros'] = "(float(a.get(1327,1)))  if  a.get(1327,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), antes de impuestos'] = "(float(a.get(788,1)))  if  a.get(788,0)  else 0"
    RATIOS[
        'Gasto por impuestos a las ganancias'] = "(float(a.get(476,1)))  if  a.get(476,0)  else 0"
    RATIOS[
        'Ganancia (pérdida) procedente de operaciones continuadas'] = "(float(a.get(774,1)))  if  a.get(774,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), atribuible a los propietarios de la controladora'] = "(float(a.get(704,1)))  if  a.get(704,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), atribuible a participaciones no controladoras'] = "(float(a.get(868,1)))  if  a.get(868,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_eerr  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_eerr  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["ESTADO RESULTADO"]

    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


def get_proyeccionbalance(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Efectivo y equivalentes al efectivo'] = "(float(a.get(739,1)))  if  (a.get(739,0))  else 0"
    RATIOS[
        'Otros activos financieros corrientes'] = "(float(a.get(607,1)))  if  a.get(607,0)  else 0"
    RATIOS[
        'Otros activos no financieros corrientes'] = "(float(a.get(835,1)))  if  a.get(835,0)  else 0"
    RATIOS[
        'Deudores comerciales y otras cuentas por cobrar corrientes'] = "(float(a.get(775,1)))  if  a.get(775,0)  else 0"
    RATIOS[
        'Cuentas por cobrar a entidades relacionadas, corrientes'] = "(float(a.get(787,1)))  if  a.get(787,0)  else 0"
    RATIOS[
        'Inventarios corrientes'] = "(float(a.get(695,1)))  if  a.get(695,0)  else 0"
    RATIOS[
        'Activos biológicos corrientes'] = "(float(a.get(1290,1)))  if  a.get(1290,0)  else 0"
    RATIOS[
        'Activos por impuestos corrientes, corrientes'] = "(float(a.get(481,1)))  if  a.get(481,0)  else 0"
    RATIOS[
        'Total de activos corrientes distintos de los activo o grupos de activos'] = "(float(a.get(797,1)))  if  a.get(797,0)  else 0"
    RATIOS[
        'Activos no corrientes o grupos de activos para su disposición clasificados'] = "(float(a.get(1291,1)))  if  a.get(1291,0)  else 0"
    RATIOS[
        'Activos corrientes totales'] = "(float(a.get(608,1)))  if  a.get(608,0)  else 0"
    RATIOS[
        'Otros activos financieros no corrientes'] = "(float(a.get(520,1)))  if  a.get(520,0)  else 0"
    RATIOS[
        'Otros activos no financieros no corrientes'] = "(float(a.get(462,1)))  if  a.get(462,0)  else 0"
    RATIOS[
        'Cuentas por cobrar no corrientes'] = "(float(a.get(753,1)))  if  a.get(753,0)  else 0"
    RATIOS[
        'Cuentas por cobrar a entidades relacionadas, no corrientes'] = "(float(a.get(680,1)))  if  a.get(680,0)  else 0"
    RATIOS[
        'Inversiones contabilizadas utilizando el método de la participación'] = "(float(a.get(713,1)))  if  a.get(713,0)  else 0"
    RATIOS[
        'Activos intangibles distintos de la plusvalía'] = "(float(a.get(748,1)))  if  a.get(748,0)  else 0"
    RATIOS[
        'Plusvalía'] = "(float(a.get(866,1)))  if  a.get(866,0)  else 0"
    RATIOS[
        'Propiedades, planta y equipo'] = "(float(a.get(456,1)))  if  a.get(456,0)  else 0"
    RATIOS[
        'Activos biológicos no corrientes'] = "(float(a.get(1294,1)))  if  a.get(1294,0)  else 0"
    RATIOS[
        'Propiedad de inversión'] = "(float(a.get(581,1)))  if  a.get(581,0)  else 0"
    RATIOS[
        'Activos por impuestos diferidos'] = "(float(a.get(622,1)))  if  a.get(622,0)  else 0"
    RATIOS[
        'Total de activos no corrientes'] = "(float(a.get(825,1)))  if  a.get(825,0)  else 0"
    RATIOS[
        'Total de activos'] = "(float(a.get(808,1)))  if  a.get(808,0)  else 0"
    RATIOS[
        'Otros pasivos financieros corrientes'] = "(float(a.get(582,1)))  if  a.get(582,0)  else 0"
    RATIOS[
        'Cuentas por pagar comerciales y otras cuentas por pagar'] = "(float(a.get(783,1)))  if  a.get(783,0)  else 0"
    RATIOS[
        'Cuentas por pagar a entidades relacionadas, corrientes'] = "(float(a.get(461,1)))  if  a.get(461,0)  else 0"
    RATIOS[
        'Otras provisiones a corto plazo'] = "(float(a.get(659,1)))  if  a.get(659,0)  else 0"
    RATIOS[
        'Pasivos por impuestos corrientes, corrientes'] = "(float(a.get(477,1)))  if  a.get(477,0)  else 0"
    RATIOS[
        'Provisiones corrientes por beneficios a los empleados'] = "(float(a.get(756,1)))  if  a.get(756,0)  else 0"
    RATIOS[
        'Otros pasivos no financieros corrientes'] = "(float(a.get(621,1)))  if  a.get(621,0)  else 0"
    RATIOS[
        'Total de pasivos corrientes distintos de los pasivos incluidos'] = "(float(a.get(745,1)))  if  a.get(745,0)  else 0"
    RATIOS[
        'Pasivos corrientes totales'] = "(float(a.get(668,1)))  if  a.get(668,0)  else 0"
    RATIOS[
        'Otros pasivos financieros no corrientes'] = "(float(a.get(791,1)))  if  a.get(791,0)  else 0"
    RATIOS[
        'Cuentas por pagar no corrientes'] = "(float(a.get(822,1)))  if  a.get(822,0)  else 0"
    RATIOS[
        'Cuentas por pagar a entidades relacionadas, no corrientes'] = "(float(a.get(486,1)))  if  a.get(486,0)  else 0"
    RATIOS[
        'Otras provisiones a largo plazo'] = "(float(a.get(524,1)))  if  a.get(524,0)  else 0"
    RATIOS[
        'Pasivo por impuestos diferidos'] = "(float(a.get(640,1)))  if  a.get(640,0)  else 0"
    RATIOS[
        'Provisiones no corrientes por beneficios a los empleados'] = "(float(a.get(629,1)))  if  a.get(629,0)  else 0"
    RATIOS[
        'Otros pasivos no financieros no corrientes'] = "(float(a.get(633,1)))  if  a.get(633,0)  else 0"
    RATIOS[
        'Total de pasivos no corrientes'] = "(float(a.get(809,1)))  if  a.get(809,0)  else 0"
    RATIOS[
        'Total de pasivos'] = "(float(a.get(519,1)))  if  a.get(519,0)  else 0"
    RATIOS[
        'Capital emitido'] = "(float(a.get(859,1)))  if  a.get(859,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) acumuladas'] = "(float(a.get(670,1)))  if  a.get(670,0)  else 0"
    RATIOS[
        'Prima de emisión'] = "(float(a.get(939,1)))  if  a.get(939,0)  else 0"
    RATIOS[
        'Acciones propias en cartera'] = "(float(a.get(1303,1)))  if  a.get(1303,0)  else 0"
    RATIOS[
        'Otras participaciones en el patrimonio'] = "(float(a.get(1304,1)))  if  a.get(1304,0)  else 0"
    RATIOS[
        'Otras reservas'] = "(float(a.get(789,1)))  if  a.get(789,0)  else 0"
    RATIOS[
        'Patrimonio atribuible a los propietarios de la controladora'] = "(float(a.get(879,1)))  if  a.get(879,0)  else 0"
    RATIOS[
        'Participaciones no controladoras'] = "(float(a.get(620,1)))  if  a.get(620,0)  else 0"
    RATIOS[
        'Patrimonio total'] = "(float(a.get(681,1)))  if  a.get(681,0)  else 0"
    RATIOS[
        'Total de patrimonio y pasivos'] = "(float(a.get(754,1)))  if  a.get(754,0)  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_proyeccionesbalance  where cod_entidad = '%s' and anio >= '2015' and mes='12'"""
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_proyeccionesbalance  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s') order by anio"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["BALANCE"]
    b = dict()
    fecha = list(range(anios[0], anios[1] + 1))
    fecha.sort()
    for anio in fecha:
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.append(resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.append((eval(RATIOS[r])))
                RESULTADO[r] = raux
        b = a
    user = session['username']
    # select a la tabla user_eerr.
    cursor.execute("select id from usuario where usuario='%s'" % (user))
    id_user = cursor.fetchone()[0]
    # consultar por id de usuario
    cursor.execute(
        "select cuenta,valor from usuario_eerr where cod_entidad='%s' and usuario='%s'" % (cod_entidad, id_user))
    resultado = cursor.fetchall()
    # GET RATIOS
    dataratios = get_ratiosdd(cod_entidad, anio, mes)[0]
    calculoratio2018 = list(dataratios)[15][1] * 0.8
    calculoratio2017 = list(dataratios)[15][2] * 0.2
    calculodiascaja = calculoratio2018 + calculoratio2017
    calculodiascobro2018 = list(dataratios)[2][1] * 0.8
    calculodiascobro2017 = list(dataratios)[2][2] * 0.2
    calculodiascobro = calculodiascobro2018 + calculodiascobro2017
    calculodiasdeinventario2018 = list(dataratios)[4][1] * 0.8
    calculodiasdeinventario2017 = list(dataratios)[4][2] * 0.2
    calculodiasdeinventario = calculodiasdeinventario2018 + calculodiasdeinventario2017
    calculodiasdepago2018 = list(dataratios)[3][1] * 0.8
    calculodiasdepago2017 = list(dataratios)[3][2] * 0.2
    calculardiasdepago = calculodiasdepago2018 + calculodiasdepago2017
    dataproyeccion = get_proyeccionEERR(cod_entidad, anio, mes)[0]
    # GET BALANCE
    Ingresos_ordinarias = float(list(dataproyeccion)[0][6])
    ganancia_perdida = list(dataproyeccion)[18][6]
    costos_ventas = list(dataproyeccion)[1][6]

    RESULTADO['Efectivo y equivalentes al efectivo'].append(
        (calculodiascaja * (Ingresos_ordinarias - ganancia_perdida) / 365))
    RESULTADO['Otros activos financieros corrientes'].append(
        RESULTADO['Otros activos financieros corrientes'][-1] * 0.8 + RESULTADO['Otros activos financieros corrientes'][
            -2] * 0.2)
    RESULTADO['Otros activos no financieros corrientes'].append(
        RESULTADO['Otros activos no financieros corrientes'][-1] * 0.8 +
        RESULTADO['Otros activos no financieros corrientes'][-2] * 0.2)
    RESULTADO['Deudores comerciales y otras cuentas por cobrar corrientes'].append(
        calculodiascobro * (Ingresos_ordinarias * 1.19) / 365)
    RESULTADO['Cuentas por cobrar a entidades relacionadas, corrientes'].append(
        RESULTADO['Cuentas por cobrar a entidades relacionadas, corrientes'][-1] * 0.8 +
        RESULTADO['Cuentas por cobrar a entidades relacionadas, corrientes'][-2] * 0.2)
    RESULTADO['Inventarios corrientes'].append((calculodiasdeinventario * costos_ventas) / 365)
    RESULTADO['Activos biológicos corrientes'].append(0)

    RESULTADO['Activos por impuestos corrientes, corrientes'].append(
        RESULTADO['Activos por impuestos corrientes, corrientes'][-1] * 0.8 +
        RESULTADO['Activos por impuestos corrientes, corrientes'][-2] * 0.2)
    RESULTADO['Total de activos corrientes distintos de los activo o grupos de activos'].append(
        RESULTADO['Efectivo y equivalentes al efectivo'][-1] + RESULTADO['Otros activos financieros corrientes'][-1] +
        RESULTADO['Otros activos no financieros corrientes'][-1]
        + RESULTADO['Deudores comerciales y otras cuentas por cobrar corrientes'][-1] +
        RESULTADO['Cuentas por cobrar a entidades relacionadas, corrientes'][-1] + RESULTADO['Inventarios corrientes'][
            -1] +
        RESULTADO['Activos biológicos corrientes'][-1] + RESULTADO['Activos por impuestos corrientes, corrientes'][-1])
    RESULTADO['Activos corrientes totales'].append(RESULTADO['Activos por impuestos corrientes, corrientes'][-1] +
                                                   RESULTADO[
                                                       'Total de activos corrientes distintos de los activo o grupos de activos'][
                                                       -1])
    RESULTADO['Activos no corrientes o grupos de activos para su disposición clasificados'].append(
        RESULTADO['Activos no corrientes o grupos de activos para su disposición clasificados'][-1] * 0.8 +
        RESULTADO['Activos no corrientes o grupos de activos para su disposición clasificados'][-2] * 0.2)
    RESULTADO['Otros activos financieros no corrientes'].append(
        RESULTADO['Otros activos financieros no corrientes'][-1] * 0.8 +
        RESULTADO['Otros activos financieros no corrientes'][-2] * 0.2)

    RESULTADO['Otros activos no financieros no corrientes'].append(
        RESULTADO['Otros activos no financieros no corrientes'][-1] * 0.8 +
        RESULTADO['Otros activos no financieros no corrientes'][-2] * 0.2)
    RESULTADO['Cuentas por cobrar no corrientes'].append(
        RESULTADO['Cuentas por cobrar no corrientes'][-1] * 0.8 + RESULTADO['Cuentas por cobrar no corrientes'][
            -2] * 0.2)

    RESULTADO['Cuentas por cobrar a entidades relacionadas, no corrientes'].append(0)
    RESULTADO['Inversiones contabilizadas utilizando el método de la participación'].append(0)

    RESULTADO['Activos intangibles distintos de la plusvalía'].append(
        RESULTADO['Activos intangibles distintos de la plusvalía'][-1] * 0.8 +
        RESULTADO['Activos intangibles distintos de la plusvalía'][-2] * 0.2)
    RESULTADO['Plusvalía'].append(0)

    RESULTADO['Propiedades, planta y equipo'].append(
        RESULTADO['Propiedades, planta y equipo'][-1] * 0.8 + RESULTADO['Propiedades, planta y equipo'][-2] * 0.2)
    RESULTADO['Activos biológicos no corrientes'].append(0)

    RESULTADO['Propiedad de inversión'].append(0)
    RESULTADO['Activos por impuestos diferidos'].append(
        RESULTADO['Activos por impuestos diferidos'][-1] * 0.8 + RESULTADO['Activos por impuestos diferidos'][-2] * 0.2)

    RESULTADO['Total de activos no corrientes'].append(RESULTADO['Otros activos financieros no corrientes'][-1] +
                                                       RESULTADO['Otros activos no financieros no corrientes'][-1] +
                                                       RESULTADO['Cuentas por cobrar no corrientes'][-1] + RESULTADO[
                                                           'Cuentas por cobrar a entidades relacionadas, no corrientes'][
                                                           -1] +
                                                       RESULTADO[
                                                           'Inversiones contabilizadas utilizando el método de la participación'][
                                                           -1] +
                                                       RESULTADO['Activos intangibles distintos de la plusvalía'][-1] +
                                                       RESULTADO['Plusvalía'][-1] +
                                                       RESULTADO['Propiedades, planta y equipo'][-1] +
                                                       RESULTADO['Activos biológicos no corrientes'][-1] +
                                                       RESULTADO['Propiedad de inversión'][-1] +
                                                       RESULTADO['Activos por impuestos diferidos'][-1])

    RESULTADO['Total de activos'].append(
        RESULTADO['Total de activos no corrientes'][-1] + RESULTADO['Activos corrientes totales'][-1])

    RESULTADO['Cuentas por pagar comerciales y otras cuentas por pagar'].append(calculardiasdepago * (
            costos_ventas + RESULTADO['Inventarios corrientes'][-2] - RESULTADO['Inventarios corrientes'][
        -1]) / 365)
    RESULTADO['Cuentas por pagar a entidades relacionadas, corrientes'].append(0)

    RESULTADO['Otras provisiones a corto plazo'].append(
        RESULTADO['Otras provisiones a corto plazo'][-1] * 0.8 + RESULTADO['Otras provisiones a corto plazo'][-2] * 0.2)
    RESULTADO['Pasivos por impuestos corrientes, corrientes'].append(
        RESULTADO['Pasivos por impuestos corrientes, corrientes'][-1] * 0.8 +
        RESULTADO['Pasivos por impuestos corrientes, corrientes'][-2] * 0.2)

    RESULTADO['Provisiones corrientes por beneficios a los empleados'].append(
        RESULTADO['Provisiones corrientes por beneficios a los empleados'][-1] * 0.8 +
        RESULTADO['Provisiones corrientes por beneficios a los empleados'][-2] * 0.2)
    RESULTADO['Otros pasivos no financieros corrientes'].append(
        RESULTADO['Otros pasivos no financieros corrientes'][-1] * 0.8 +
        RESULTADO['Otros pasivos no financieros corrientes'][-2] * 0.2)
    RESULTADO['Otros pasivos financieros no corrientes'].append(
        RESULTADO['Otros pasivos financieros no corrientes'][-1] * 0.9)
    RESULTADO['Cuentas por pagar no corrientes'].append(0)
    RESULTADO['Cuentas por pagar a entidades relacionadas, no corrientes'].append(0)
    RESULTADO['Otras provisiones a largo plazo'].append(0)

    RESULTADO['Pasivo por impuestos diferidos'].append(
        RESULTADO['Pasivo por impuestos diferidos'][-1] * 0.8 + RESULTADO['Pasivo por impuestos diferidos'][-2] * 0.2)
    RESULTADO['Provisiones no corrientes por beneficios a los empleados'].append(0)
    RESULTADO['Otros pasivos no financieros no corrientes'].append(0)
    RESULTADO['Total de pasivos no corrientes'].append(
        RESULTADO['Otros pasivos financieros no corrientes'][-1] + RESULTADO['Pasivo por impuestos diferidos'][-1])
    RESULTADO['Capital emitido'].append(RESULTADO['Capital emitido'][-1])
    RESULTADO['Ganancias (pérdidas) acumuladas'].append(
        RESULTADO['Ganancias (pérdidas) acumuladas'][-1] + ganancia_perdida)
    RESULTADO['Prima de emisión'].append(0)
    RESULTADO['Acciones propias en cartera'].append(0)
    RESULTADO['Otras participaciones en el patrimonio'].append(0)

    RESULTADO['Otras reservas'].append(RESULTADO['Otras reservas'][-1])
    RESULTADO['Patrimonio atribuible a los propietarios de la controladora'].append(
        RESULTADO['Capital emitido'][-1] + RESULTADO['Ganancias (pérdidas) acumuladas'][-1] +
        RESULTADO['Otras reservas'][-1])

    RESULTADO['Participaciones no controladoras'].append(RESULTADO['Participaciones no controladoras'][-1])
    RESULTADO['Patrimonio total'].append(RESULTADO['Participaciones no controladoras'][-1] +
                                         RESULTADO['Patrimonio atribuible a los propietarios de la controladora'][-1])

    RESULTADO['Otros pasivos financieros corrientes'].append(0)

    RESULTADO['Total de pasivos corrientes distintos de los pasivos incluidos'].append(
        # RESULTADO['Otros pasivos financieros corrientes'][-1] +
        RESULTADO['Cuentas por pagar comerciales y otras cuentas por pagar'][-1] +
        RESULTADO['Cuentas por pagar a entidades relacionadas, corrientes'][-1] +
        RESULTADO['Otras provisiones a corto plazo'][-1] +
        RESULTADO['Pasivos por impuestos corrientes, corrientes'][-1] +
        RESULTADO['Provisiones corrientes por beneficios a los empleados'][-1] +
        RESULTADO['Otros pasivos no financieros corrientes'][-1]
    )
    RESULTADO['Pasivos corrientes totales'].append(
        RESULTADO['Total de pasivos corrientes distintos de los pasivos incluidos'][-1])
    RESULTADO['Total de pasivos'].append(
        RESULTADO['Total de pasivos no corrientes'][-1] + RESULTADO['Pasivos corrientes totales'][-1])
    RESULTADO['Total de patrimonio y pasivos'].append(
        RESULTADO['Total de pasivos'][-1] + RESULTADO['Patrimonio total'][-1])
    RESULTADO['Otros pasivos financieros corrientes'].append(
        RESULTADO['Total de activos'][-1] - RESULTADO['Total de patrimonio y pasivos'][-1])
    COLUMNAS.append("Proyección")
    return RESULTADO.values(), COLUMNAS


@app.route('/ProyeccionBalance/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def ProyeccionBalance(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    data, columnas = get_proyeccionbalance(cod_entidad, anio, mes)
    data2, columnas2 = get_proyeccionRatios(cod_entidad, anio, mes)
    empresa = request.args.get("empresa")
    return render_template("/ProyeccionBalance.html", entidad=entidad, data=list(data), columnas=columnas,
                           empresa=empresa, cod_entidad=cod_entidad, data2=data2, columnas2=columnas2)


def get_proyeccionEERR(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades ordinarias'] = "(float(a.get(540,1)))"
    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)))  if  a.get(727,0)  else 0"
    RATIOS[
        'Ganancias Bruta'] = "(float(a.get(805,1)))  if  a.get(805,0)  else 0"
    RATIOS[
        'Otros Ingresos'] = "(float(a.get(682,1)))  if  a.get(682,0)  else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,1)))  if  a.get(1324,0)  else 0"
    RATIOS[
        'Gastos de administración'] = "(float(a.get(618,1)))  if  a.get(618,0)  else 0"
    RATIOS[
        'Otros gastos, por función'] = "(float(a.get(1325,1)))  if  a.get(1325,0)  else 0"
    RATIOS[
        'Otras ganancias (pérdidas)'] = "(float(a.get(815,1)))  if  a.get(815,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) de actividades operacionales'] = "(float(a.get(817,1)))  if  a.get(817,0)  else 0"
    RATIOS[
        'Ingresos financieros'] = "(float(a.get(558,1)))  if  a.get(558,0)  else 0"
    RATIOS[
        'Costos financieros'] = "(float(a.get(764,1)))  if  a.get(764,0)  else 0"
    RATIOS[
        'Participación en las ganancias (pérdidas) de asociadas y negocios'] = "(float(a.get(824,1)))  if  a.get(824,0)  else 0"
    RATIOS[
        'Diferencias de cambio'] = "(float(a.get(849,1)))  if  a.get(849,0)  else 0"
    RATIOS[
        'Resultados por unidades de reajuste'] = "(float(a.get(516,1)))  if  a.get(516,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) que surgen de diferencias entre importes en libros'] = "(float(a.get(1327,1)))  if  a.get(1327,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), antes de impuestos'] = "(float(a.get(788,1)))  if  a.get(788,0)  else 0"
    RATIOS[
        'Gasto por impuestos a las ganancias'] = "(float(a.get(476,1)))  if  a.get(476,0)  else 0"
    RATIOS[
        'Ganancia (pérdida) procedente de operaciones continuadas'] = "(float(a.get(774,1)))  if  a.get(774,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), atribuible a los propietarios de la controladora'] = "(float(a.get(704,1)))  if  a.get(704,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), atribuible a participaciones no controladoras'] = "(float(a.get(868,1)))  if  a.get(868,0)  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_proyeccioneerr  where cod_entidad = '%s' and anio >= '2015' and mes='12'"""
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_proyeccioneerr  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s') order by anio"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["PROYECCION ESTADO RESULTADO"]
    b = dict()
    fecha = list(range(anios[0], anios[1] + 1))
    fecha.sort()
    for anio in fecha:
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.append(resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.append((eval(RATIOS[r])))
                RESULTADO[r] = raux
        b = a
    p = list(RESULTADO.values())
    per = int(anio) + 1
    anterior = None
    factor = [0.05, 0.15, 0.8]
    asignado = 0
    for i in range(1, len(p[0])):
        if anterior:
            # ACTUAL
            process = (p[0][i] - anterior) / anterior
            print(process, factor[i - 2])
            asignado += process * factor[i - 2]
        anterior = p[0][i]

    user = session['username']
    # select a la tabla user_eerr.
    cursor.execute("select id from usuario where usuario='%s'" % (user))
    id_user = cursor.fetchone()[0]
    # consultar por id de usuario
    cursor.execute(
        "select cuenta,valor from usuario_eerr where cod_entidad='%s' and usuario='%s'" % (cod_entidad, id_user))
    resultado = cursor.fetchall()

    # append a las tabla de proyeccion con dos nuevos campos
    RESULTADO['Ingresos de Actividades ordinarias'].append(0)
    RESULTADO['Ingresos de Actividades ordinarias'].append(dict(resultado).get('Ingresos de Actividades ordinarias',
                                                                               float(RESULTADO[
                                                                                         'Ingresos de Actividades ordinarias'][
                                                                                         -2]) * asignado +
                                                                               RESULTADO[
                                                                                   'Ingresos de Actividades ordinarias'][
                                                                                   -2]))
    RESULTADO['Costos de Ventas'].append(
        dict(resultado).get('Costos de Ventas', float(RESULTADO['Costos de Ventas'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Costos de Ventas'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos de Ventas'][-1]))
    RESULTADO['Ganancias Bruta'].append(dict(resultado).get('Ganancias Bruta', RESULTADO['Ganancias Bruta'][-1] /
                                                            RESULTADO['Ingresos de Actividades ordinarias'][-3]))
    RESULTADO['Ganancias Bruta'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-1]))
    RESULTADO['Otros Ingresos'].append(dict(resultado).get('Otros Ingresos', RESULTADO['Otros Ingresos'][-1] /
                                                           float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Otros Ingresos'].append(0)
    RESULTADO['Costos de Distribucion'].append(0)
    RESULTADO['Costos de Distribucion'].append(0)
    RESULTADO['Gastos de administración'].append(dict(resultado).get('Gastos de administración',
                                                                     RESULTADO['Gastos de administración'][-1] /
                                                                     RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -3]))
    RESULTADO['Gastos de administración'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Gastos de administración'][-1]))
    RESULTADO['Otros gastos, por función'].append(dict(resultado).get('Otros gastos, por función',
                                                                      float(
                                                                          RESULTADO['Otros gastos, por función'][-1]) /
                                                                      float(RESULTADO[
                                                                                'Ingresos de Actividades ordinarias'][
                                                                                -1])))
    RESULTADO['Otros gastos, por función'].append(0)
    RESULTADO['Otras ganancias (pérdidas)'].append(0)
    RESULTADO['Otras ganancias (pérdidas)'].append(0)
    RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
        dict(resultado).get('Ganancias (pérdidas) de actividades operacionales',
                            RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-1] /
                            RESULTADO['Ingresos de Actividades ordinarias'][-3]))
    RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
        RESULTADO['Ganancias Bruta'][-1] - float(RESULTADO['Gastos de administración'][-1]))
    RESULTADO['Ingresos financieros'].append(0)
    RESULTADO['Ingresos financieros'].append(0)
    RESULTADO['Costos financieros'].append(dict(resultado).get('Costos financieros',
                                                               float(RESULTADO['Costos financieros'][-1]) /
                                                               float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -1])))
    RESULTADO['Costos financieros'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos financieros'][-1]))
    RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
    RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
    RESULTADO['Diferencias de cambio'].append(dict(resultado).get('Diferencias de cambio',
                                                                  float(RESULTADO['Diferencias de cambio'][-1]) /
                                                                  float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                            -3])))
    RESULTADO['Diferencias de cambio'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Diferencias de cambio'][-1]))
    RESULTADO['Resultados por unidades de reajuste'].append(dict(resultado).get('Resultados por unidades de reajuste',
                                                                                float(RESULTADO[
                                                                                          'Resultados por unidades de reajuste'][
                                                                                          -1]) / float(RESULTADO[
                                                                                                           'Ingresos de Actividades ordinarias'][
                                                                                                           -3])))
    RESULTADO['Resultados por unidades de reajuste'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(
            RESULTADO['Resultados por unidades de reajuste'][-1]))
    RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
    RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
    RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
        dict(resultado).get('Ganancia (pérdida), antes de impuestos',
                            float(RESULTADO['Ganancia (pérdida), antes de impuestos'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
        RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-1] - RESULTADO['Costos financieros'][-1] +
        RESULTADO['Diferencias de cambio'][-1] - RESULTADO['Resultados por unidades de reajuste'][-1])
    RESULTADO['Gasto por impuestos a las ganancias'].append(dict(resultado).get('Gasto por impuestos a las ganancias',
                                                                                float(RESULTADO[
                                                                                          'Gasto por impuestos a las ganancias'][
                                                                                          -1]) / float(RESULTADO[
                                                                                                           'Ingresos de Actividades ordinarias'][
                                                                                                           -3])))
    RESULTADO['Gasto por impuestos a las ganancias'].append(
        RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] * 0.27)
    RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
        dict(resultado).get('Ganancia (pérdida) procedente de operaciones continuadas',
                            float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
        RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] + float(
            RESULTADO['Gasto por impuestos a las ganancias'][-1]))
    RESULTADO['Ganancia (pérdida)'].append(dict(resultado).get('Ganancia (pérdida)',
                                                               float(RESULTADO['Ganancia (pérdida)'][-1]) /
                                                               float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -3])))
    RESULTADO['Ganancia (pérdida)'].append(
        float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-1]))
    RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(
        dict(resultado).get('Ganancia (pérdida), atribuible a los propietarios de la controladora',
                            float(
                                RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
    RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(
        dict(resultado).get('Ganancia (pérdida), atribuible a participaciones no controladoras',
                            float(RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
    COLUMNAS.append("%")
    COLUMNAS.append("Proyección Un Año")

    print(request.method)
    if request.method == 'POST':
        if request.form.get('Proyectar'):
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * asignado +
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]))
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * asignado +
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]))

            RESULTADO['Costos de Ventas'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(RESULTADO['Costos de Ventas'][-2]))
            RESULTADO['Costos de Ventas'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos de Ventas'][-3]))

            RESULTADO['Ganancias Bruta'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-1]))
            RESULTADO['Ganancias Bruta'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-2]))
            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Gastos de administración'].append(float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * (
                float(RESULTADO['Gastos de administración'][-2])))
            RESULTADO['Gastos de administración'].append(float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * (
                float(RESULTADO['Gastos de administración'][-3])))

            RESULTADO['Otros gastos, por función'].append(0)
            RESULTADO['Otros gastos, por función'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                float(RESULTADO['Ganancias Bruta'][-2]) - float(RESULTADO['Gastos de administración'][-2]))
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                float(RESULTADO['Ganancias Bruta'][-1]) - float(RESULTADO['Gastos de administración'][-1]))
            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Costos financieros'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(RESULTADO['Costos financieros'][-2]))
            RESULTADO['Costos financieros'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos financieros'][-3]))
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Diferencias de cambio'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(
                    RESULTADO['Diferencias de cambio'][-2]))
            RESULTADO['Diferencias de cambio'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(
                    RESULTADO['Diferencias de cambio'][-3]))
            RESULTADO['Resultados por unidades de reajuste'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(
                    RESULTADO['Resultados por unidades de reajuste'][-2]))
            RESULTADO['Resultados por unidades de reajuste'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(
                    RESULTADO['Resultados por unidades de reajuste'][-3]))
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                float(RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-2]) - float(
                    RESULTADO['Costos financieros'][-2])
                + float(RESULTADO['Diferencias de cambio'][-2]) - float(
                    RESULTADO['Resultados por unidades de reajuste'][-2]))
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                float(RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-1]) - float(
                    RESULTADO['Costos financieros'][-1])
                + float(RESULTADO['Diferencias de cambio'][-1]) - float(
                    RESULTADO['Resultados por unidades de reajuste'][-1]))
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-2] * 0.27)
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] * 0.27)
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-2] + float(
                    RESULTADO['Gasto por impuestos a las ganancias'][-2]))
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-3] + float(
                    RESULTADO['Gasto por impuestos a las ganancias'][-3]))
            RESULTADO['Ganancia (pérdida)'].append(
                float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-2]))
            RESULTADO['Ganancia (pérdida)'].append(
                float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-1]))
            RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            COLUMNAS.append("Proyección Dos Años")
            COLUMNAS.append("Proyección Tres Años")

        elif request.form.get('ProyectarCinco'):
            # proyectadouno = float(asignado * 0.2)
            # proyectadodos = float(proyectadouno * 0.2)
            # proyectadotres = float(proyectadodos * 0.2)
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * asignado +
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]))
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * asignado +
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]))
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * asignado +
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]))
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * asignado +
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]))

            RESULTADO['Costos de Ventas'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-4]) * float(RESULTADO['Costos de Ventas'][-2]))
            RESULTADO['Costos de Ventas'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-3]) * float(RESULTADO['Costos de Ventas'][-3]))
            RESULTADO['Costos de Ventas'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(RESULTADO['Costos de Ventas'][-4]))
            RESULTADO['Costos de Ventas'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos de Ventas'][-5]))

            RESULTADO['Ganancias Bruta'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-1]))
            RESULTADO['Ganancias Bruta'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-2]))
            RESULTADO['Ganancias Bruta'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-3]))
            RESULTADO['Ganancias Bruta'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-4]))
            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Otros Ingresos'].append(0)

            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)

            RESULTADO['Gastos de administración'].append(float(RESULTADO['Ingresos de Actividades ordinarias'][-4]) * (
                float(RESULTADO['Gastos de administración'][-2])))
            RESULTADO['Gastos de administración'].append(float(RESULTADO['Ingresos de Actividades ordinarias'][-3]) * (
                float(RESULTADO['Gastos de administración'][-3])))
            RESULTADO['Gastos de administración'].append(float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * (
                float(RESULTADO['Gastos de administración'][-4])))
            RESULTADO['Gastos de administración'].append(float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * (
                float(RESULTADO['Gastos de administración'][-5])))

            RESULTADO['Otros gastos, por función'].append(0)
            RESULTADO['Otros gastos, por función'].append(0)
            RESULTADO['Otros gastos, por función'].append(0)

            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)

            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                float(RESULTADO['Ganancias Bruta'][-4]) - float(RESULTADO['Gastos de administración'][-4]))
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                float(RESULTADO['Ganancias Bruta'][-3]) - float(RESULTADO['Gastos de administración'][-3]))
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                float(RESULTADO['Ganancias Bruta'][-2]) - float(RESULTADO['Gastos de administración'][-2]))
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                float(RESULTADO['Ganancias Bruta'][-1]) - float(RESULTADO['Gastos de administración'][-1]))

            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Ingresos financieros'].append(0)

            RESULTADO['Costos financieros'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-4]) * float(RESULTADO['Costos financieros'][-2]))
            RESULTADO['Costos financieros'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-3]) * float(RESULTADO['Costos financieros'][-3]))
            RESULTADO['Costos financieros'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(RESULTADO['Costos financieros'][-4]))
            RESULTADO['Costos financieros'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos financieros'][-5]))

            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)

            RESULTADO['Diferencias de cambio'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-4]) * float(
                    RESULTADO['Diferencias de cambio'][-2]))
            RESULTADO['Diferencias de cambio'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-3]) * float(
                    RESULTADO['Diferencias de cambio'][-3]))
            RESULTADO['Diferencias de cambio'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(
                    RESULTADO['Diferencias de cambio'][-4]))
            RESULTADO['Diferencias de cambio'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(
                    RESULTADO['Diferencias de cambio'][-5]))

            RESULTADO['Resultados por unidades de reajuste'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-4]) * float(
                    RESULTADO['Resultados por unidades de reajuste'][-2]))
            RESULTADO['Resultados por unidades de reajuste'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-3]) * float(
                    RESULTADO['Resultados por unidades de reajuste'][-3]))
            RESULTADO['Resultados por unidades de reajuste'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-2]) * float(
                    RESULTADO['Resultados por unidades de reajuste'][-4]))
            RESULTADO['Resultados por unidades de reajuste'].append(
                float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(
                    RESULTADO['Resultados por unidades de reajuste'][-5]))

            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)

            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                float(RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4]) - float(
                    RESULTADO['Costos financieros'][-4])
                + float(RESULTADO['Diferencias de cambio'][-4]) - float(
                    RESULTADO['Resultados por unidades de reajuste'][-4]))
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                float(RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-3]) - float(
                    RESULTADO['Costos financieros'][-3])
                + float(RESULTADO['Diferencias de cambio'][-3]) - float(
                    RESULTADO['Resultados por unidades de reajuste'][-3]))
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                float(RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-2]) - float(
                    RESULTADO['Costos financieros'][-2])
                + float(RESULTADO['Diferencias de cambio'][-2]) - float(
                    RESULTADO['Resultados por unidades de reajuste'][-2]))
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                float(RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-1]) - float(
                    RESULTADO['Costos financieros'][-1])
                + float(RESULTADO['Diferencias de cambio'][-1]) - float(
                    RESULTADO['Resultados por unidades de reajuste'][-1]))

            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-4] * 0.27)
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-3] * 0.27)
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-2] * 0.27)
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] * 0.27)

            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-4] + float(
                    RESULTADO['Gasto por impuestos a las ganancias'][-4]))
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-3] + float(
                    RESULTADO['Gasto por impuestos a las ganancias'][-3]))
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-2] + float(
                    RESULTADO['Gasto por impuestos a las ganancias'][-2]))
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] + float(
                    RESULTADO['Gasto por impuestos a las ganancias'][-1]))

            RESULTADO['Ganancia (pérdida)'].append(
                float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4]))
            RESULTADO['Ganancia (pérdida)'].append(
                float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-3]))
            RESULTADO['Ganancia (pérdida)'].append(
                float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-2]))
            RESULTADO['Ganancia (pérdida)'].append(
                float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-1]))

            RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)

            RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)

            COLUMNAS.append("Proyección Dos Años")
            COLUMNAS.append("Proyección Tres Años")
            COLUMNAS.append("Proyección Cuatro Años")
            COLUMNAS.append("Proyección Cinco Años")
    return RESULTADO.values(), COLUMNAS


def get_proyeccionEERR2(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades ordinarias'] = "(float(a.get(540,1)))"
    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)))  if  a.get(727,0)  else 0"
    RATIOS[
        'Ganancias Bruta'] = "(float(a.get(805,1)))  if  a.get(805,0)  else 0"
    RATIOS[
        'Otros Ingresos'] = "(float(a.get(682,1)))  if  a.get(682,0)  else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,1)))  if  a.get(1324,0)  else 0"
    RATIOS[
        'Gastos de administración'] = "(float(a.get(618,1)))  if  a.get(618,0)  else 0"
    RATIOS[
        'Otros gastos, por función'] = "(float(a.get(1325,1)))  if  a.get(1325,0)  else 0"
    RATIOS[
        'Otras ganancias (pérdidas)'] = "(float(a.get(815,1)))  if  a.get(815,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) de actividades operacionales'] = "(float(a.get(817,1)))  if  a.get(817,0)  else 0"
    RATIOS[
        'Ingresos financieros'] = "(float(a.get(558,1)))  if  a.get(558,0)  else 0"
    RATIOS[
        'Costos financieros'] = "(float(a.get(764,1)))  if  a.get(764,0)  else 0"
    RATIOS[
        'Participación en las ganancias (pérdidas) de asociadas y negocios'] = "(float(a.get(824,1)))  if  a.get(824,0)  else 0"
    RATIOS[
        'Diferencias de cambio'] = "(float(a.get(849,1)))  if  a.get(849,0)  else 0"
    RATIOS[
        'Resultados por unidades de reajuste'] = "(float(a.get(516,1)))  if  a.get(516,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) que surgen de diferencias entre importes en libros'] = "(float(a.get(1327,1)))  if  a.get(1327,0)  else 0"
    RATIOS[
        'Ganancia (pérdida), antes de impuestos'] = "(float(a.get(788,1)))  if  a.get(788,0)  else 0"
    RATIOS[
        'Gasto por impuestos a las ganancias'] = "(float(a.get(476,1)))  if  a.get(476,0)  else 0"
    RATIOS[
        'Ganancia (pérdida) procedente de operaciones continuadas'] = "(float(a.get(774,1)))  if  a.get(774,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"
    # RATIOS[
    #     'Ganancia (pérdida), atribuible a los propietarios de la controladora'] = "(float(a.get(704,1)))  if  a.get(704,0)  else 0"
    # RATIOS[
    #     'Ganancia (pérdida), atribuible a participaciones no controladoras'] = "(float(a.get(868,1)))  if  a.get(868,0)  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_proyeccioneerr  where cod_entidad = '%s' and anio >= '2015' and mes='12'"""
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_proyeccioneerr  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s') order by anio"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["PROYECCION ESTADO RESULTADO"]
    b = dict()
    fecha = list(range(anios[0], anios[1] + 1))
    fecha.sort()
    for anio in fecha:
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.append(resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.append((eval(RATIOS[r])))
                RESULTADO[r] = raux
        b = a
    p = list(RESULTADO.values())
    per = int(anio) + 1
    anterior = None
    factor = [0.05, 0.15, 0.8]
    asignado = 0
    for i in range(1, len(p[0])):
        if anterior:
            # ACTUAL
            process = (p[0][i] - anterior) / anterior
            print(process, factor[i - 2])
            asignado += process * factor[i - 2]
        anterior = p[0][i]

    user = session['username']
    # select a la tabla user_eerr.
    cursor.execute("select id from usuario where usuario='%s'" % (user))
    id_user = cursor.fetchone()[0]
    # consultar por id de usuario
    cursor.execute(
        "select cuenta,valor from usuario_eerr where cod_entidad='%s' and usuario='%s'" % (cod_entidad, id_user))
    resultado = cursor.fetchall()
    # append a las tabla de proyeccion con dos nuevos campos
    RESULTADO['Ingresos de Actividades ordinarias'].append(0)
    RESULTADO['Ingresos de Actividades ordinarias'].append(dict(resultado).get('Ingresos de Actividades ordinarias',
                                                                               float(RESULTADO[
                                                                                         'Ingresos de Actividades ordinarias'][
                                                                                         -2]) * asignado +
                                                                               RESULTADO[
                                                                                   'Ingresos de Actividades ordinarias'][
                                                                                   -2]))
    RESULTADO['Costos de Ventas'].append(
        dict(resultado).get('Costos de Ventas', float(RESULTADO['Costos de Ventas'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Costos de Ventas'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos de Ventas'][-1]))
    RESULTADO['Ganancias Bruta'].append(dict(resultado).get('Ganancias Bruta', RESULTADO['Ganancias Bruta'][-1] /
                                                            RESULTADO['Ingresos de Actividades ordinarias'][-3]))
    RESULTADO['Ganancias Bruta'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) - float(RESULTADO['Costos de Ventas'][-1]))

    if dict(resultado).get('Otros Ingresos'):
        RESULTADO['Otros Ingresos'].append(dict(resultado).get('Otros Ingresos', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) / float(RESULTADO['Otros Ingresos'][-1])))
        RESULTADO['Costos de Distribucion'].append(float(dict(resultado).get('Otros Ingresos')) * float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]))

    elif RESULTADO['Otros Ingresos'][-1]:
        RESULTADO['Otros Ingresos'].append(dict(resultado).get('Otros Ingresos', RESULTADO['Otros Ingresos'][-1] /
                                                               float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -3])))
        RESULTADO['Otros Ingresos'].append(dict(resultado).get('Otros Ingresos', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Otros Ingresos'][-1])))
    else:
        RESULTADO['Otros Ingresos'].append(0)
        RESULTADO['Otros Ingresos'].append(0)

    if dict(resultado).get('Costos de Distribucion'):
        RESULTADO['Costos de Distribucion'].append(dict(resultado).get('Costos de Distribucion', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) / float(RESULTADO['Costos de Distribucion'][-1])))
        RESULTADO['Costos de Distribucion'].append(float(dict(resultado).get('Costos de Distribucion')) * float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]))
    elif RESULTADO['Costos de Distribucion'][-2]:
        RESULTADO['Costos de Distribucion'].append(dict(resultado).get('Costos de Distribucion', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos de Distribucion'][-1])))
        RESULTADO['Costos de Distribucion'].append(dict(resultado).get('Costos de Distribucion', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos de Distribucion'][-2])))
    else:
        RESULTADO['Costos de Distribucion'].append(0)
        RESULTADO['Costos de Distribucion'].append(0)

    RESULTADO['Gastos de administración'].append(dict(resultado).get('Gastos de administración',
                                                                     RESULTADO['Gastos de administración'][-1] /
                                                                     RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -3]))
    RESULTADO['Gastos de administración'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Gastos de administración'][-1]))

    if dict(resultado).get('Otros gastos, por función'):
        RESULTADO['Otros gastos, por función'].append(dict(resultado).get('Otros gastos, por función',
                                                                      float(
                                                                          RESULTADO['Otros gastos, por función'][-1]) /
                                                                      float(RESULTADO[
                                                                                'Ingresos de Actividades ordinarias'][
                                                                                -1])))
        RESULTADO['Otros gastos, por función'].append(float(dict(resultado).get('Otros gastos, por función')) * float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]))

    elif RESULTADO['Otros gastos, por función'][-2]:
        RESULTADO['Otros gastos, por función'].append(dict(resultado).get('Otros gastos, por función', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Otros gastos, por función'][-1])))
        RESULTADO['Otros gastos, por función'].append(dict(resultado).get('Otros gastos, por función', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Otros gastos, por función'][-2])))
    else:
        RESULTADO['Otros gastos, por función'].append(0)
        RESULTADO['Otros gastos, por función'].append(0)

    if RESULTADO['Otras ganancias (pérdidas)'][-1]:
        RESULTADO['Otras ganancias (pérdidas)'].append(dict(resultado).get('Otras ganancias (pérdidas)', float(
            RESULTADO['Otras ganancias (pérdidas)'][-1]) / float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
        RESULTADO['Otras ganancias (pérdidas)'].append(dict(resultado).get('Otras ganancias (pérdidas)', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Otras ganancias (pérdidas)'][-1])))
    else:
        RESULTADO['Otras ganancias (pérdidas)'].append(0)
        RESULTADO['Otras ganancias (pérdidas)'].append(0)

    RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
        dict(resultado).get('Ganancias (pérdidas) de actividades operacionales',
                            RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-1] /
                            RESULTADO['Ingresos de Actividades ordinarias'][-3]))
    RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
        RESULTADO['Ganancias Bruta'][-1] - float(RESULTADO['Gastos de administración'][-1]))

    if dict(resultado).get('Ingresos financieros'):
        RESULTADO['Ingresos financieros'].append(dict(resultado).get('Ingresos financieros',
                                                                      float(
                                                                          RESULTADO['Ingresos financieros'][-1]) /
                                                                      float(RESULTADO[
                                                                                'Ingresos de Actividades ordinarias'][
                                                                                -1])))
        RESULTADO['Ingresos financieros'].append(float(dict(resultado).get('Ingresos financieros')) * float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]))

    elif RESULTADO['Ingresos financieros'][-2]:
        RESULTADO['Ingresos financieros'].append(dict(resultado).get('Ingresos financieros', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Ingresos financieros'][-1])))
        RESULTADO['Ingresos financieros'].append(dict(resultado).get('Ingresos financieros', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Ingresos financieros'][-2])))
    else:
        RESULTADO['Ingresos financieros'].append(0)
        RESULTADO['Ingresos financieros'].append(0)

    RESULTADO['Costos financieros'].append(dict(resultado).get('Costos financieros',
                                                               float(RESULTADO['Costos financieros'][-1]) /
                                                               float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -1])))
    RESULTADO['Costos financieros'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Costos financieros'][-1]))

    if dict(resultado).get('Participación en las ganancias (pérdidas) de asociadas y negocios'):
        RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(dict(resultado).get('Participación en las ganancias (pérdidas) de asociadas y negocios',
                                                                      float(
                                                                          RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'][-1]) /
                                                                      float(RESULTADO[
                                                                                'Ingresos de Actividades ordinarias'][
                                                                                -1])))
        RESULTADO['Ingresos financieros'].append(float(dict(resultado).get('Participación en las ganancias (pérdidas) de asociadas y negocios')) * float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]))

    elif RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'][-2]:
        RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(dict(resultado).get('Participación en las ganancias (pérdidas) de asociadas y negocios', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'][-1])))
        RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(dict(resultado).get('Participación en las ganancias (pérdidas) de asociadas y negocios', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'][-2])))
    else:
        RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
        RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)

    RESULTADO['Diferencias de cambio'].append(dict(resultado).get('Diferencias de cambio',
                                                                  float(RESULTADO['Diferencias de cambio'][-1]) /
                                                                  float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                            -3])))
    RESULTADO['Diferencias de cambio'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Diferencias de cambio'][-1]))
    RESULTADO['Resultados por unidades de reajuste'].append(dict(resultado).get('Resultados por unidades de reajuste',
                                                                                float(RESULTADO[
                                                                                          'Resultados por unidades de reajuste'][
                                                                                          -1]) / float(RESULTADO[
                                                                                                           'Ingresos de Actividades ordinarias'][
                                                                                                           -3])))
    RESULTADO['Resultados por unidades de reajuste'].append(
        float(RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(
            RESULTADO['Resultados por unidades de reajuste'][-1]))

    if dict(resultado).get('Ganancias (pérdidas) que surgen de diferencias entre importes en libros'):
        RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(dict(resultado).get('Ganancias (pérdidas) que surgen de diferencias entre importes en libros',
                                                                      float(
                                                                          RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'][-1]) /
                                                                      float(RESULTADO[
                                                                                'Ingresos de Actividades ordinarias'][
                                                                                -1])))
        RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(float(dict(resultado).get('Ganancias (pérdidas) que surgen de diferencias entre importes en libros')) * float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]))

    elif RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'][-2]:
        RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(dict(resultado).get('Ganancias (pérdidas) que surgen de diferencias entre importes en libros', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'][-1])))
        RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(dict(resultado).get('Ganancias (pérdidas) que surgen de diferencias entre importes en libros', float(
            RESULTADO['Ingresos de Actividades ordinarias'][-1]) * float(RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'][-2])))
    else:
        RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
        RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
    RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
        dict(resultado).get('Ganancia (pérdida), antes de impuestos',
                            float(RESULTADO['Ganancia (pérdida), antes de impuestos'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
        RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-1] - RESULTADO['Costos financieros'][-1] +
        RESULTADO['Diferencias de cambio'][-1] - RESULTADO['Resultados por unidades de reajuste'][-1])
    RESULTADO['Gasto por impuestos a las ganancias'].append(dict(resultado).get('Gasto por impuestos a las ganancias',
                                                                                float(RESULTADO[
                                                                                          'Gasto por impuestos a las ganancias'][
                                                                                          -1]) / float(RESULTADO[
                                                                                                           'Ingresos de Actividades ordinarias'][
                                                                                                           -3])))
    RESULTADO['Gasto por impuestos a las ganancias'].append(
        RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] * 0.27)
    RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
        dict(resultado).get('Ganancia (pérdida) procedente de operaciones continuadas',
                            float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-1]) /
                            float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
        RESULTADO['Ganancia (pérdida), antes de impuestos'][-1] + float(
            RESULTADO['Gasto por impuestos a las ganancias'][-1]))
    RESULTADO['Ganancia (pérdida)'].append(dict(resultado).get('Ganancia (pérdida)',
                                                               float(RESULTADO['Ganancia (pérdida)'][-1]) /
                                                               float(RESULTADO['Ingresos de Actividades ordinarias'][
                                                                         -3])))
    RESULTADO['Ganancia (pérdida)'].append(
        float(RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-1]))
    # RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(
    #     dict(resultado).get('Ganancia (pérdida), atribuible a los propietarios de la controladora',
    #                         float(
    #                             RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'][-1]) /
    #                         float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    # RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
    # RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(
    #     dict(resultado).get('Ganancia (pérdida), atribuible a participaciones no controladoras',
    #                         float(RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'][-1]) /
    #                         float(RESULTADO['Ingresos de Actividades ordinarias'][-3])))
    # RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
    COLUMNAS.append("%")
    COLUMNAS.append("Proyección Un Año")
    print(request.method)
    if request.method == 'POST':
        if request.form.get('Proyectar'):
            primero = ((RESULTADO['Ingresos de Actividades ordinarias'][-4] /
                        RESULTADO['Ingresos de Actividades ordinarias'][-5]) - 1)
            segundo = ((RESULTADO['Ingresos de Actividades ordinarias'][-3] /
                        RESULTADO['Ingresos de Actividades ordinarias'][-4]) - 1)
            porcentaje = (primero + segundo) / 2
            RESULTADO['Ingresos de Actividades ordinarias'].append(porcentaje)
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                RESULTADO['Ingresos de Actividades ordinarias'][-4] * (porcentaje + 1))

            primero1 = ((RESULTADO['Costos de Ventas'][-4] /
                         RESULTADO['Costos de Ventas'][-5]) - 1)
            segundo1 = ((RESULTADO['Costos de Ventas'][-3] /
                         RESULTADO['Costos de Ventas'][-4]) - 1)
            porcentaje1 = (primero1 + segundo1) / 2
            RESULTADO['Costos de Ventas'].append(porcentaje1)
            RESULTADO['Costos de Ventas'].append(
                RESULTADO['Costos de Ventas'][-4] * (porcentaje1 + 1))

            primero2 = ((RESULTADO['Ganancias Bruta'][-4] /
                         RESULTADO['Ganancias Bruta'][-5]) - 1)
            segundo2 = ((RESULTADO['Ganancias Bruta'][-3] /
                         RESULTADO['Ganancias Bruta'][-4]) - 1)
            porcentaje2 = (primero2 + segundo2) / 2
            RESULTADO['Ganancias Bruta'].append(porcentaje2)
            RESULTADO['Ganancias Bruta'].append(
                RESULTADO['Ganancias Bruta'][-4] * (porcentaje2 + 1))

            # if dict(resultado).get('Otros Ingresos'):
            #     prim = ((RESULTADO['Otros Ingresos'][-4] /
            #              RESULTADO['Otros Ingresos'][-5]) - 1)
            #     seg = ((RESULTADO['Otros Ingresos'][-3] /
            #              RESULTADO['Otros Ingresos'][-4]) - 1)
            #     porc = (prim + seg) / 2
            #     RESULTADO['Otros Ingresos'].append(porc)
            #     RESULTADO['Otros Ingresos'].append(
            #         RESULTADO['Otros Ingresos'][-4] * (porc + 1))
            #
            # elif RESULTADO['Otros Ingresos'][-1]:
            #     prim = ((RESULTADO['Otros Ingresos'][-4] /
            #              RESULTADO['Otros Ingresos'][-5]) - 1)
            #     seg = ((RESULTADO['Otros Ingresos'][-3] /
            #             RESULTADO['Otros Ingresos'][-4]) - 1)
            #     porc = (prim + seg) / 2
            #     RESULTADO['Otros Ingresos'].append(porc)
            #     RESULTADO['Otros Ingresos'].append(
            #         RESULTADO['Otros Ingresos'][-4] * (porc + 1))
            # else:
            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Otros Ingresos'].append(0)


            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)

            primero3 = ((RESULTADO['Gastos de administración'][-4] /
                         RESULTADO['Gastos de administración'][-5]) - 1)
            segundo3 = ((RESULTADO['Gastos de administración'][-3] /
                         RESULTADO['Gastos de administración'][-4]) - 1)
            porcentaje3 = (primero3 + segundo3) / 2
            RESULTADO['Gastos de administración'].append(porcentaje3)
            RESULTADO['Gastos de administración'].append(
                RESULTADO['Gastos de administración'][-4] * (porcentaje3 + 1))

            RESULTADO['Otros gastos, por función'].append(0)
            RESULTADO['Otros gastos, por función'].append(0)

            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)

            primero4 = ((RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4] /
                         RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-5]) - 1)
            segundo4 = ((RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-3] /
                         RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4]) - 1)
            porcentaje4 = (primero4 + segundo4) / 2
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(porcentaje4)
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4] * (porcentaje4 + 1))

            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Ingresos financieros'].append(0)

            primero5 = ((RESULTADO['Costos financieros'][-4] /
                         RESULTADO['Costos financieros'][-5]) - 1)
            segundo5 = ((RESULTADO['Costos financieros'][-3] /
                         RESULTADO['Costos financieros'][-4]) - 1)
            porcentaje5 = (primero5 + segundo5) / 2
            RESULTADO['Costos financieros'].append(porcentaje5)
            RESULTADO['Costos financieros'].append(
                RESULTADO['Costos financieros'][-4] * (porcentaje5 + 1))

            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)

            primero6 = ((RESULTADO['Diferencias de cambio'][-4] /
                         RESULTADO['Diferencias de cambio'][-5]) - 1)
            segundo6 = ((RESULTADO['Diferencias de cambio'][-3] /
                         RESULTADO['Diferencias de cambio'][-4]) - 1)
            porcentaje6 = (primero6 + segundo6) / 2
            RESULTADO['Diferencias de cambio'].append(porcentaje6)
            RESULTADO['Diferencias de cambio'].append(
                RESULTADO['Diferencias de cambio'][-4] * (porcentaje6 + 1))

            primero7 = ((RESULTADO['Resultados por unidades de reajuste'][-4] /
                         RESULTADO['Resultados por unidades de reajuste'][-5]) - 1)
            segundo7 = ((RESULTADO['Resultados por unidades de reajuste'][-3] /
                         RESULTADO['Resultados por unidades de reajuste'][-4]) - 1)
            porcentaje7 = (primero7 + segundo7) / 2
            RESULTADO['Resultados por unidades de reajuste'].append(porcentaje7)
            RESULTADO['Resultados por unidades de reajuste'].append(
                RESULTADO['Resultados por unidades de reajuste'][-4] * (porcentaje7 + 1))

            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)

            primero8 = ((RESULTADO['Ganancia (pérdida), antes de impuestos'][-4] /
                         RESULTADO['Ganancia (pérdida), antes de impuestos'][-5]) - 1)
            segundo8 = ((RESULTADO['Ganancia (pérdida), antes de impuestos'][-3] /
                         RESULTADO['Ganancia (pérdida), antes de impuestos'][-4]) - 1)
            porcentaje8 = (primero8 + segundo8) / 2
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(porcentaje8)
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-4] * (porcentaje8 + 1))

            primero9 = ((RESULTADO['Gasto por impuestos a las ganancias'][-4] /
                         RESULTADO['Gasto por impuestos a las ganancias'][-5]) - 1)
            segundo9 = ((RESULTADO['Gasto por impuestos a las ganancias'][-3] /
                         RESULTADO['Gasto por impuestos a las ganancias'][-4]) - 1)
            porcentaje9 = (primero9 + segundo9) / 2
            RESULTADO['Gasto por impuestos a las ganancias'].append(porcentaje9)
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Gasto por impuestos a las ganancias'][-4] * (porcentaje9 + 1))

            primero10 = ((RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4] /
                          RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-5]) - 1)
            segundo10 = ((RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-3] /
                          RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4]) - 1)
            porcentaje10 = (primero10 + segundo10) / 2
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(porcentaje10)
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4] * (porcentaje10 + 1))

            primero11 = ((RESULTADO['Ganancia (pérdida)'][-4] /
                          RESULTADO['Ganancia (pérdida)'][-5]) - 1)
            segundo11 = ((RESULTADO['Ganancia (pérdida)'][-3] /
                          RESULTADO['Ganancia (pérdida)'][-4]) - 1)
            porcentaje11 = (primero11 + segundo11) / 2
            RESULTADO['Ganancia (pérdida)'].append(porcentaje11)
            RESULTADO['Ganancia (pérdida)'].append(
                RESULTADO['Ganancia (pérdida)'][-4] * (porcentaje11 + 1))

            # RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            # RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            # 
            # RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            # RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            COLUMNAS.append("% PROYECTADO")
            COLUMNAS.append("Proyección Tres Años")

        if request.form.get('ProyectarCinco'):
            primero = ((RESULTADO['Ingresos de Actividades ordinarias'][-5] /
                        RESULTADO['Ingresos de Actividades ordinarias'][-6]) - 1)
            segundo = ((RESULTADO['Ingresos de Actividades ordinarias'][-4] /
                        RESULTADO['Ingresos de Actividades ordinarias'][-5]) - 1)
            tercero = ((RESULTADO['Ingresos de Actividades ordinarias'][-3] /
                        RESULTADO['Ingresos de Actividades ordinarias'][-4]) - 1)
            porcentaje = (primero + segundo + tercero) / 3
            RESULTADO['Ingresos de Actividades ordinarias'].append(porcentaje)
            RESULTADO['Ingresos de Actividades ordinarias'].append(
                RESULTADO['Ingresos de Actividades ordinarias'][-4] * (porcentaje + 1))

            primero1 = ((RESULTADO['Costos de Ventas'][-5] /
                         RESULTADO['Costos de Ventas'][-6]) - 1)
            segundo1 = ((RESULTADO['Costos de Ventas'][-4] /
                         RESULTADO['Costos de Ventas'][-5]) - 1)
            tercero1 = ((RESULTADO['Costos de Ventas'][-3] /
                         RESULTADO['Costos de Ventas'][-4]) - 1)
            porcentaje1 = (primero1 + segundo1 + tercero1) / 3
            RESULTADO['Costos de Ventas'].append(porcentaje1)
            RESULTADO['Costos de Ventas'].append(
                RESULTADO['Costos de Ventas'][-4] * (porcentaje1 + 1))

            primero2 = ((RESULTADO['Ganancias Bruta'][-5] /
                         RESULTADO['Ganancias Bruta'][-6]) - 1)
            segundo2 = ((RESULTADO['Ganancias Bruta'][-4] /
                         RESULTADO['Ganancias Bruta'][-5]) - 1)
            tercero2 = ((RESULTADO['Ganancias Bruta'][-3] /
                         RESULTADO['Ganancias Bruta'][-4]) - 1)
            porcentaje2 = (primero2 + segundo2 + tercero2) / 3
            RESULTADO['Ganancias Bruta'].append(porcentaje2)
            RESULTADO['Ganancias Bruta'].append(
                RESULTADO['Ganancias Bruta'][-4] * (porcentaje2 + 1))

            RESULTADO['Otros Ingresos'].append(0)
            RESULTADO['Otros Ingresos'].append(0)

            RESULTADO['Costos de Distribucion'].append(0)
            RESULTADO['Costos de Distribucion'].append(0)

            primero3 = ((RESULTADO['Gastos de administración'][-5] /
                         RESULTADO['Gastos de administración'][-6]) - 1)
            segundo3 = ((RESULTADO['Gastos de administración'][-4] /
                         RESULTADO['Gastos de administración'][-5]) - 1)
            tercero3 = ((RESULTADO['Gastos de administración'][-3] /
                         RESULTADO['Gastos de administración'][-4]) - 1)
            porcentaje3 = (primero3 + segundo3 + tercero3) / 3
            RESULTADO['Gastos de administración'].append(porcentaje3)
            RESULTADO['Gastos de administración'].append(
                RESULTADO['Gastos de administración'][-4] * (porcentaje3 + 1))

            RESULTADO['Otros gastos, por función'].append(0)
            RESULTADO['Otros gastos, por función'].append(0)

            RESULTADO['Otras ganancias (pérdidas)'].append(0)
            RESULTADO['Otras ganancias (pérdidas)'].append(0)

            primero4 = ((RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-5] /
                         RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-6]) - 1)
            segundo4 = ((RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4] /
                         RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-5]) - 1)
            tercero4 = ((RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-3] /
                         RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4]) - 1)
            porcentaje4 = (primero4 + segundo4 + tercero4) / 3
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(porcentaje4)
            RESULTADO['Ganancias (pérdidas) de actividades operacionales'].append(
                RESULTADO['Ganancias (pérdidas) de actividades operacionales'][-4] * (porcentaje4 + 1))

            RESULTADO['Ingresos financieros'].append(0)
            RESULTADO['Ingresos financieros'].append(0)
            primero5 = ((RESULTADO['Costos financieros'][-5] /
                         RESULTADO['Costos financieros'][-6]) - 1)
            segundo5 = ((RESULTADO['Costos financieros'][-4] /
                         RESULTADO['Costos financieros'][-5]) - 1)
            tercero5 = ((RESULTADO['Costos financieros'][-3] /
                         RESULTADO['Costos financieros'][-4]) - 1)
            porcentaje5 = (primero5 + segundo5 + tercero5) / 3
            RESULTADO['Costos financieros'].append(porcentaje5)
            RESULTADO['Costos financieros'].append(
                RESULTADO['Costos financieros'][-4] * (porcentaje5 + 1))

            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)
            RESULTADO['Participación en las ganancias (pérdidas) de asociadas y negocios'].append(0)

            primero6 = ((RESULTADO['Diferencias de cambio'][-5] /
                         RESULTADO['Diferencias de cambio'][-6]) - 1)
            segundo6 = ((RESULTADO['Diferencias de cambio'][-4] /
                         RESULTADO['Diferencias de cambio'][-5]) - 1)
            tercero6 = ((RESULTADO['Diferencias de cambio'][-3] /
                         RESULTADO['Diferencias de cambio'][-4]) - 1)
            porcentaje6 = (primero6 + segundo6 + tercero6) / 3
            RESULTADO['Diferencias de cambio'].append(porcentaje6)
            RESULTADO['Diferencias de cambio'].append(
                RESULTADO['Diferencias de cambio'][-4] * (porcentaje6 + 1))

            primero7 = ((RESULTADO['Resultados por unidades de reajuste'][-5] /
                         RESULTADO['Resultados por unidades de reajuste'][-6]) - 1)
            segundo7 = ((RESULTADO['Resultados por unidades de reajuste'][-4] /
                         RESULTADO['Resultados por unidades de reajuste'][-5]) - 1)
            tercero7 = ((RESULTADO['Resultados por unidades de reajuste'][-3] /
                         RESULTADO['Resultados por unidades de reajuste'][-4]) - 1)
            porcentaje7 = (primero7 + segundo7 + tercero7) / 3
            RESULTADO['Resultados por unidades de reajuste'].append(porcentaje7)
            RESULTADO['Resultados por unidades de reajuste'].append(
                RESULTADO['Resultados por unidades de reajuste'][-4] * (porcentaje7 + 1))

            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)
            RESULTADO['Ganancias (pérdidas) que surgen de diferencias entre importes en libros'].append(0)

            primero8 = ((RESULTADO['Ganancia (pérdida), antes de impuestos'][-5] /
                         RESULTADO['Ganancia (pérdida), antes de impuestos'][-6]) - 1)
            segundo8 = ((RESULTADO['Ganancia (pérdida), antes de impuestos'][-4] /
                         RESULTADO['Ganancia (pérdida), antes de impuestos'][-5]) - 1)
            tercero8 = ((RESULTADO['Ganancia (pérdida), antes de impuestos'][-3] /
                         RESULTADO['Ganancia (pérdida), antes de impuestos'][-4]) - 1)
            porcentaje8 = (primero8 + segundo8 + tercero8) / 3
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(porcentaje8)
            RESULTADO['Ganancia (pérdida), antes de impuestos'].append(
                RESULTADO['Ganancia (pérdida), antes de impuestos'][-4] * (porcentaje8 + 1))

            primero9 = ((RESULTADO['Gasto por impuestos a las ganancias'][-5] /
                         RESULTADO['Gasto por impuestos a las ganancias'][-6]) - 1)
            segundo9 = ((RESULTADO['Gasto por impuestos a las ganancias'][-4] /
                         RESULTADO['Gasto por impuestos a las ganancias'][-5]) - 1)
            tercero9 = ((RESULTADO['Gasto por impuestos a las ganancias'][-3] /
                         RESULTADO['Gasto por impuestos a las ganancias'][-4]) - 1)
            porcentaje9 = (primero9 + segundo9 + tercero9) / 3
            RESULTADO['Gasto por impuestos a las ganancias'].append(porcentaje9)
            RESULTADO['Gasto por impuestos a las ganancias'].append(
                RESULTADO['Gasto por impuestos a las ganancias'][-4] * (porcentaje9 + 1))

            primero10 = ((RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4] /
                          RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-5]) - 1)
            segundo10 = ((RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-3] /
                          RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4]) - 1)
            porcentaje10 = (primero10 + segundo10) / 2
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(porcentaje10)
            RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'].append(
                RESULTADO['Ganancia (pérdida) procedente de operaciones continuadas'][-4] * (porcentaje10 + 1))

            primero11 = ((RESULTADO['Ganancia (pérdida)'][-4] /
                          RESULTADO['Ganancia (pérdida)'][-5]) - 1)
            segundo11 = ((RESULTADO['Ganancia (pérdida)'][-3] /
                          RESULTADO['Ganancia (pérdida)'][-4]) - 1)
            porcentaje11 = (primero11 + segundo11) / 3
            RESULTADO['Ganancia (pérdida)'].append(porcentaje11)
            RESULTADO['Ganancia (pérdida)'].append(
                RESULTADO['Ganancia (pérdida)'][-4] * (porcentaje11 + 1))

            # RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            # RESULTADO['Ganancia (pérdida), atribuible a los propietarios de la controladora'].append(0)
            # 
            # RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            # RESULTADO['Ganancia (pérdida), atribuible a participaciones no controladoras'].append(0)
            COLUMNAS.append("% PROYECTADO")
            COLUMNAS.append("Proyección Cinco Años")
    return RESULTADO.values(), COLUMNAS


# actualizacion de valores en tabla de proyeccion estados de resultados.
@app.route('/porcentaje_estado_resultado/<cuenta>/<valor>/<entidad>', methods=['GET', 'POST'])
def actualizacion(cuenta, valor, entidad):
    cursor = cnx.cursor()
    valor = float(valor.replace(",", ""))
    user = session['username']
    cursor.execute("select id from usuario where usuario='%s'" % (user))
    id_user = cursor.fetchone()[0]
    cursor.execute(
        """select usuario,cuenta from usuario_eerr where usuario='%s' and cuenta='%s' and cod_entidad='%s'""" % (
            id_user, cuenta, entidad))
    test = cursor.fetchall()
    if test:
        cursor.execute(
            """update usuario_eerr set valor ='%s' where usuario='%s' and cuenta='%s' and cod_entidad='%s'""" % (
                valor, id_user, cuenta, entidad))
        cnx.commit()
    else:
        cursor.execute(
            """insert into usuario_eerr (usuario, cuenta, valor,cod_entidad) values ('%s','%s','%s','%s')""" % (
                id_user, cuenta, valor, entidad))
        cnx.commit()
    return ("cuenta actualizada")


@app.route('/porcentaje_ratios/<cuenta>/<valor>/<entidad>', methods=['GET', 'POST'])
def actualizacionratios(cuenta, valor, entidad):
    cursor = cnx.cursor()
    valor = float(valor.replace(",", ""))
    user = session['username']
    cursor.execute("select id from usuario where usuario='%s'" % (user))
    id_user = cursor.fetchone()[0]
    cursor.execute(
        """select usuario,cuenta from usuario_eerr where usuario='%s' and cuenta='%s' and cod_entidad='%s'""" % (
            id_user, cuenta, entidad))
    test = cursor.fetchall()
    if test:
        cursor.execute(
            """update usuario_eerr set valor ='%s' where usuario='%s' and cuenta='%s' and cod_entidad='%s'""" % (
                valor, id_user, cuenta, entidad))
        cnx.commit()
    else:
        cursor.execute(
            """insert into usuario_eerr (usuario, cuenta, valor,cod_entidad) values ('%s','%s','%s','%s')""" % (
                id_user, cuenta, valor, entidad))
        cnx.commit()
    return ("cuenta actualizada")

# Proyeccion estados de resultados
@app.route('/ProyeccionEERR2/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def ProyeccionEERR2(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        empresa = request.args.get("empresa")
        data, columnas = get_proyeccionEERR2(cod_entidad, anio, mes)
        empresa = request.args.get("empresa")
        p = list(data)
        per = int(anio) + 1
        anterior = None
        factor = [0.05, 0.15, 0.8]
        asignado = 0
        for i in range(1, len(p[0])):
            if anterior:
                # ACTUAL
                process = (p[0][i] - anterior) / anterior
                print(process, factor[i - 2])
                asignado += process * factor[i - 2]
                if p[0][0] == 'Ingresos de Actividades ordinarias':
                    ingresos = p[0][0]
            anterior = p[0][i]
        return render_template("/ProyeccionEERR2.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data), columnas1=columnas, cod_entidad=cod_entidad, empresa=empresa,
                               asignado=asignado, per=per)
    data, columnas = get_proyeccionEERR2(cod_entidad, anio, mes)
    empresa = request.args.get("empresa")
    return render_template("/ProyeccionEERR2.html", entidad=entidad, data=list(data), columnas=columnas,
                           empresa=empresa, cod_entidad=cod_entidad)


# valorización
@app.route('/ProyeccionEERR1/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def ProyeccionEERR1(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        empresa = request.args.get("empresa")
        data, columnas = get_proyeccionEERR(cod_entidad, anio, mes)
        empresa = request.args.get("empresa")
        p = list(data)
        per = int(anio) + 1
        anterior = None
        factor = [0.05, 0.15, 0.8]
        asignado = 0
        for i in range(1, len(p[0])):
            if anterior:
                # ACTUAL
                process = (p[0][i] - anterior) / anterior
                print(process, factor[i - 2])
                asignado += process * factor[i - 2]
                if p[0][0] == 'Ingresos de Actividades ordinarias':
                    ingresos = p[0][0]
            anterior = p[0][i]
        return render_template("/ProyeccionEERR.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data), columnas1=columnas, cod_entidad=cod_entidad, empresa=empresa,
                               asignado=asignado, per=per)
    data, columnas = get_proyeccionEERR(cod_entidad, anio, mes)
    empresa = request.args.get("empresa")
    return render_template("/ProyeccionEERR1.html", entidad=entidad, data=list(data), columnas=columnas,
                           empresa=empresa, cod_entidad=cod_entidad)


# pagina estados de resutlados
@app.route('/eresultado/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def eresultado(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        data1, columnas1 = get_eresultado(cod_entidad, anio, mes)
        return render_template("/eresultado.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad)
    data, columnas = get_eresultado(cod_entidad, anio, mes)
    empresa = request.args.get("empresa")
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(empresa, anio)
        return render_template("/eresultado.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data1), columnas1=columnas1, en=en, empresa=empresa)
    return render_template("/eresultado.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa,
                           cod_entidad=cod_entidad)


# impresión de memos según empresa
@app.route('/memo/<cod_documento>/<cod_role>', methods=["GET", "POST"])
def memo(cod_documento, cod_role):
    cursor = cnx.cursor()
    cursor.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, desc_detalle_documento valor 
            from detalle_documento 
            join cuenta using (cod_cuenta) 
            left join role_cuenta using (cod_cuenta)
            left join role using(cod_role)
            left join unidad using (cod_unidad)
            join tipo_cuenta using (cod_tipo_cuenta)
            join contexto using (cod_contexto) 
            join entidad using (cod_entidad)
            join periodo using (cod_periodo) 
            left join context_escenarios using (cod_contexto) 
            left join escenario using (cod_escenario) 
            left join dimension using (cod_dimension) 
            --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
            where cod_dimension is null  and cod_documento = %s and cod_role =%s
            order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role))
    data = dictfetchall(cursor)
    cursor.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, case when not decimales isnull then desc_detalle_documento::numeric / 10 ^ abs(decimales) else 0 end valor 
                                    from detalle_documento 
                                    join cuenta using (cod_cuenta) 
                                    left join role_cuenta using (cod_cuenta)
                                    left join role using(cod_role)
                                    left join unidad using (cod_unidad)
                                    join tipo_cuenta using (cod_tipo_cuenta)
                                    join contexto using (cod_contexto) 
                                    join entidad using (cod_entidad)
                                    join periodo using (cod_periodo) 
                                    left join context_escenarios using (cod_contexto) 
                                    left join escenario using (cod_escenario) 
                                    left join dimension using (cod_dimension) 
                                    --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
                                    where cod_dimension is null  and cod_documento = %s and cod_role =%s
                                    order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role))
    date = cursor.fetchall()
    cursor.execute("""select distinct desc_periodo 
                                   from detalle_documento 
                                   join cuenta using (cod_cuenta) 
                                   left join role_cuenta using (cod_cuenta)
                                   left join role using(cod_role)
                                   join contexto using (cod_contexto) 
                                   join periodo using (cod_periodo)
                                   left join context_escenarios using (cod_contexto) 
                                   left join escenario using (cod_escenario) 
                                   left join dimension using (cod_dimension)
                                   where cod_dimension is null  and cod_documento = %s and cod_role =%s
                                   order by desc_periodo desc""" % (cod_documento, cod_role))
    per = dictfetchall(cursor)
    CI = set_CI()

    for d in date:
        cod_rol = d[1]
        desc_role = d[0]
        entidad = d[13]
        cuenta = d[5]
        dineros = d[8]
        fechas = d[7]
    hoy = datetime.now()
    hoy = hoy.strftime("%Y-%m-%d")
    report = PdfCustomDetail(filename="%s.pdf" % (cod_rol), title=["%s" % (desc_role), entidad.__str__(), cuenta],
                             logo=getattr(sys, 'logo', 'xeeffy_logo_index.png'))
    pvt_kms = pivot(data, ('cod_role_cuenta', 'desc_cuenta'), ('desc_periodo',), 'valor')
    datas = []
    columnas = ["CUENTA"]
    data_linea = ['']
    ancho_total = 0
    colsWidth = [0]
    colAlign = ['LEFT']
    colType = ['str']
    for p in per:
        columnas.append(p['desc_periodo'])
        data_linea.append(0.0)
        colsWidth.append(60)
        ancho_total += 60
        colAlign.append("RIGHT")
        colType.append("str")
    colsWidth[0] = 540 - ancho_total
    for f in pvt_kms:
        dl = list(f.get(('cod_role_cuenta', 'desc_cuenta'), ['']))
        for p in per:
            dl.append(f.get((p['desc_periodo'],), 0))
        datas.append(dl)
    data_final = []
    datas.sort()
    for d in datas:
        data_final.append(d[1:])
    return render_template("/memo.html", d=data_final, columnas=columnas, entidad=entidad, desc_role=desc_role,
                           hoy=hoy)


# funciones para el import de CMF
def set_CI():
    return getattr(sys, 'membrete', [['', 0]])
    try:

        CI = [[sys.__getattribute__('license')['company'].replace("\xd1", "Ñ"), 0],
              ["RUT:" + sys.__getattribute__('license')['rut_empresa'], 1],
              ["GIRO:" + sys.__getattribute__('license')['giro'], 2],
              [sys.__getattribute__('license')['direccion'] + ", " + sys.__getattribute__('license')['comuna'], 3]]
    except:
        CI = [["", 0]]
    return CI


# reporte de uso y fuentes cargados desde la misma pagina
@app.route('/usoyfuentes/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def usoyfuentes(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    anio = int(anio)
    aniom = int(anio) - 1
    RATIO = {}
    RATIO['Efectivo y Equivalente'] = {'DIVIDENDO': 739, 'DIVISOR': 739, 'VALOR': 0}
    RATIO['Otros Activos Financieros'] = {'DIVIDENDO': 607, 'DIVISOR': 607, 'VALOR': 0}
    RATIO['Otros Activos No Financieros'] = {'DIVIDENDO': 835, 'DIVISOR': 835, 'VALOR': 0}
    RATIO['Deudores Comerciales'] = {'DIVIDENDO': 775, 'DIVISOR': 775, 'VALOR': 0}
    RATIO['Cuentas por Cobrar'] = {'DIVIDENDO': 787, 'DIVISOR': 787, 'VALOR': 0}
    RATIO['Inventarios Corrientes'] = {'DIVIDENDO': 695, 'DIVISOR': 695, 'VALOR': 0}
    RATIO['Activos Biologicos Corrientes'] = {'DIVIDENDO': 1290, 'DIVISOR': 1290, 'VALOR': 0}
    RATIO['Activos por Impuestos Corrientes'] = {'DIVIDENDO': 481, 'DIVISOR': 481, 'VALOR': 0}
    RATIO['Total Activos Corrientes'] = {'DIVIDENDO': 797, 'DIVISOR': 797, 'VALOR': 0}
    RATIO['Activos no Corrientes'] = {'DIVIDENDO': 1291, 'DIVISOR': 1291, 'VALOR': 0}
    RATIO['Activos Corrientes Totales'] = {'DIVIDENDO': 608, 'DIVISOR': 608, 'VALOR': 0}
    RATIO['Activos no Corrientes Periodicos'] = {'DIVIDENDO': 1292, 'DIVISOR': 1292, 'VALOR': 0}
    RATIO['Otros Activos Financieros no Corriente'] = {'DIVIDENDO': 520, 'DIVISOR': 520, 'VALOR': 0}
    RATIO['Otros Activos no Financieros no Corrientes '] = {'DIVIDENDO': 462, 'DIVISOR': 462, 'VALOR': 0}
    RATIO['Cuentas por Cobrar no Corrientes'] = {'DIVIDENDO': 753, 'DIVISOR': 753, 'VALOR': 0}
    RATIO['Cuentas por Cobrar a Entidades'] = {'DIVIDENDO': 680, 'DIVISOR': 680, 'VALOR': 0}
    RATIO['Inventarios no Corrientes'] = {'DIVIDENDO': 1293, 'DIVISOR': 1293, 'VALOR': 0}
    RATIO['Inversiones Contabilizadas'] = {'DIVIDENDO': 713, 'DIVISOR': 713, 'VALOR': 0}
    RATIO['Activos Intangibles'] = {'DIVIDENDO': 748, 'DIVISOR': 748, 'VALOR': 0}
    RATIO['Plusvalia'] = {'DIVIDENDO': 866, 'DIVISOR': 866, 'VALOR': 0}
    RATIO['Propiedades Plantas y Equipo'] = {'DIVIDENDO': 456, 'DIVISOR': 466, 'VALOR': 0}
    RATIO['Activos Biologicos no Corrientes'] = {'DIVIDENDO': 1294, 'DIVISOR': 1294, 'VALOR': 0}
    RATIO['Propiedad de Inversion'] = {'DIVIDENDO': 581, 'DIVISOR': 581, 'VALOR': 0}
    RATIO['Activos por Impuestos Corrientes, no Corrientes'] = {'DIVIDENDO': 1295, 'DIVISOR': 1295, 'VALOR': 0}
    RATIO['Activos por Impuestos Diferidos'] = {'DIVIDENDO': 622, 'DIVISOR': 622, 'VALOR': 0}
    RATIO['Total Activos no Corrientes'] = {'DIVIDENDO': 825, 'DIVISOR': 825, 'VALOR': 0}
    RATIO['Total Activos'] = {'DIVIDENDO': 808, 'DIVISOR': 808, 'VALOR': 0}
    RATIO['Patrimonios y Pasivos'] = {'DIVIDENDO': 1296, 'DIVISOR': 1296, 'VALOR': 0}
    RATIO['Pasivos'] = {'DIVIDENDO': 1297, 'DIVISOR': 1297, 'VALOR': 0}
    RATIO['Pasivos Corrientes'] = {'DIVIDENDO': 1298, 'DIVISOR': 1298, 'VALOR': 0}
    RATIO['Otros Pasivos Financieros Corrientes'] = {'DIVIDENDO': 582, 'DIVISOR': 582, 'VALOR': 0}
    RATIO['Cuentas por Pagar Comerciales'] = {'DIVIDENDO': 783, 'DIVISOR': 783, 'VALOR': 0}
    RATIO['Cuentas por Pagar a Entidades Relacionadas'] = {'DIVIDENDO': 461, 'DIVISOR': 461, 'VALOR': 0}
    RATIO['Otras Provisiones a Corto Plazo'] = {'DIVIDENDO': 659, 'DIVISOR': 659, 'VALOR': 0}
    RATIO['Pasivos por Impuestos Corrientes'] = {'DIVIDENDO': 477, 'DIVISOR': 477, 'VALOR': 0}
    RATIO['Provisiones Corrientes por Beneficios'] = {'DIVIDENDO': 756, 'DIVISOR': 756, 'VALOR': 0}
    RATIO['Otros Pasivos no Financieros Corrientes'] = {'DIVIDENDO': 621, 'DIVISOR': 621, 'VALOR': 0}
    RATIO['Total de pasivos corrientes'] = {'DIVIDENDO': 745, 'DIVISOR': 745, 'VALOR': 0}
    RATIO['Pasivos incluidos en grupos de activos'] = {'DIVIDENDO': 1299, 'DIVISOR': 1299, 'VALOR': 0}
    RATIO['Pasivos corrientes totales'] = {'DIVIDENDO': 668, 'DIVISOR': 668, 'VALOR': 0}
    RATIO['Pasivos no corrientes [sinopsis]'] = {'DIVIDENDO': 1300, 'DIVISOR': 1300, 'VALOR': 0}
    RATIO['Otros pasivos financieros no corrientes'] = {'DIVIDENDO': 791, 'DIVISOR': 791, 'VALOR': 0}
    RATIO['Cuentas por pagar no corrientes'] = {'DIVIDENDO': 822, 'DIVISOR': 822, 'VALOR': 0}
    RATIO['Cuentas por pagar a entidades relacionadas'] = {'DIVIDENDO': 486, 'DIVISOR': 486, 'VALOR': 0}
    RATIO['Otras provisiones a largo plazo'] = {'DIVIDENDO': 524, 'DIVISOR': 524, 'VALOR': 0}
    RATIO['Pasivo por impuestos diferidos'] = {'DIVIDENDO': 640, 'DIVISOR': 640, 'VALOR': 0}
    RATIO['Pasivos por impuestos corrientes, no corrientes'] = {'DIVIDENDO': 1301, 'DIVISOR': 1301, 'VALOR': 0}
    RATIO['Provisiones no corrientes por beneficios a los empleados'] = {'DIVIDENDO': 629, 'DIVISOR': 629, 'VALOR': 0}
    RATIO['Otros pasivos no financieros no corrientes'] = {'DIVIDENDO': 633, 'DIVISOR': 633, 'VALOR': 0}
    RATIO['Total de pasivos no corrientes'] = {'DIVIDENDO': 809, 'DIVISOR': 809, 'VALOR': 0}
    RATIO['Total de pasivos'] = {'DIVIDENDO': 519, 'DIVISOR': 519, 'VALOR': 0}
    RATIO['Patrimonio sinopsis'] = {'DIVIDENDO': 1302, 'DIVISOR': 1302, 'VALOR': 0}
    RATIO['Ganancias (pérdidas) acumuladas'] = {'DIVIDENDO': 670, 'DIVISOR': 670, 'VALOR': 0}
    RATIO['Prima de emisión'] = {'DIVIDENDO': 939, 'DIVISOR': 939, 'VALOR': 0}
    RATIO['Acciones propias en cartera'] = {'DIVIDENDO': 1303, 'DIVISOR': 1303, 'VALOR': 0}
    RATIO['Otras participaciones en el patrimonio'] = {'DIVIDENDO': 1304, 'DIVISOR': 1304, 'VALOR': 0}
    RATIO['Otras reservas'] = {'DIVIDENDO': 789, 'DIVISOR': 789, 'VALOR': 0}
    RATIO['Patrimonio atribuible a los propietarios'] = {'DIVIDENDO': 879, 'DIVISOR': 879, 'VALOR': 0}
    RATIO['Participaciones no controladoras'] = {'DIVIDENDO': 620, 'DIVISOR': 620, 'VALOR': 0}
    RATIO['Patrimonio total'] = {'DIVIDENDO': 681, 'DIVISOR': 681, 'VALOR': 0}
    RATIO['Total de patrimonio y pasivos'] = {'DIVIDENDO': 754, 'DIVISOR': 754, 'VALOR': 0}

    aniop = request.args.get("aniop")
    if aniop:
        for k in RATIO:
            aniopm = int(aniop) - 1
            SQL = """select(select valor from usoyfuentes INNER JOIN documento USING (cod_documento) WHERE documento.cod_entidad = '%s' and usoyfuentes.anio = '%s' and cod_cuenta = '%s' and usoyfuentes.mes='%s') -
                     (select valor from usoyfuentes INNER JOIN documento USING (cod_documento) WHERE documento.cod_entidad = '%s' and usoyfuentes.anio = '%s' and cod_cuenta = '%s' and usoyfuentes.mes='%s')""" % (
                cod_entidad, aniop, RATIO[k]['DIVIDENDO'], mes, cod_entidad, aniopm, RATIO[k]['DIVISOR'], mes)
            cursor.execute(SQL)
            RATIO[k]['VALOR'] = CMon(cursor.fetchone()[0])
            cursor.execute(
                """SELECT DISTINCT
                * from entidad where cod_entidad ='%s'""" % (
                    cod_entidad))
        entidad = cursor.fetchone()[1]
        return render_template("/usoyfuentes.html", RATIO=RATIO, entidad=entidad, mes=mes, anio=aniop, aniom=aniopm,
                               cod_entidad=cod_entidad)
    for k in RATIO:
        SQL = """select(select valor from usoyfuentes INNER JOIN documento USING (cod_documento) WHERE documento.cod_entidad = '%s' and usoyfuentes.anio = '%s' and cod_cuenta = '%s' and usoyfuentes.mes='%s') -
         (select valor from usoyfuentes INNER JOIN documento USING (cod_documento) WHERE documento.cod_entidad = '%s' and usoyfuentes.anio = '%s' and cod_cuenta = '%s' and usoyfuentes.mes='%s')""" % (
            cod_entidad, anio, RATIO[k]['DIVIDENDO'], mes, cod_entidad, aniom, RATIO[k]['DIVISOR'], mes)
        cursor.execute(SQL)
        RATIO[k]['VALOR'] = CMon(cursor.fetchone()[0])
        cursor.execute(
            """SELECT DISTINCT
            * from entidad where cod_entidad ='%s'""" % (
                cod_entidad))
    entidad = cursor.fetchone()[1]
    return render_template("/usoyfuentes.html", RATIO=RATIO, entidad=entidad, mes=mes, anio=anio, aniom=aniom,
                           cod_entidad=cod_entidad)


# pago con paypal no implementado aún
@app.route('/paypal', methods=["GET", "POST"])
def paypal():
    return render_template("/paypal.html")


# proyeccion estado resultado no ocupada
@app.route('/ProyeccionEERR/<cod_entidad>/<anio>', methods=["GET", "POST"])
def ProyeccionEERR(cod_entidad, anio):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    data, columnas = get_eerr(cod_entidad, anio)
    empresa = request.args.get("empresa")
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(empresa, anio)
        return render_template("/ProyeccionEERR.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data1), columnas1=columnas1, en=en, empresa=empresa)
    return render_template("/ProyeccionEERR.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa)


def get_proyeccionRatios(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    RATIOS = {}
    RATIOS[
        'Dias de Caja'] = "((float(a.get(739) or 0) / (float(a.get(540) or 1) - float(a.get(479)))) * 365) if (a.get(739,0) and a.get(540,0) and a.get(479)) else 0"
    RATIOS[
        'Dias De Cobro'] = "(float(a.get(775) or 0) / float(a.get(540) or 0) * float(1.19))* float(365) if (a.get(775,0) and a.get(540,0)) else 0"
    RATIOS[
        'Dias de Inventarios'] = "((float(a.get(695) or 0) / float(a.get(727) or 0)) * float(365)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'Dias De Pago'] = "(float(a.get(783) or 0) / (float(a.get(727) or 0) + float(a.get(695) or 0) - float(b.get(695) or 0)))*365 if (a.get(783,0) and a.get(727,0)and b.get(695,0)) else 0"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_proyeccionesbalance  where cod_entidad = '%s' and anio >= '2015' and mes='12'"""
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad))
    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_proyeccionesbalance  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s') order by anio"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["BALANCE"]
    b = dict()
    fecha = list(range(anios[0], anios[1] + 1))
    fecha.sort()
    for anio in fecha:
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.append(resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.append((eval(RATIOS[r])))
                RESULTADO[r] = raux
        b = a
    user = session['username']
    # select a la tabla user_eerr.
    cursor.execute("select id from usuario where usuario='%s'" % (user))
    id_user = cursor.fetchone()[0]
    # consultar por id de usuario
    cursor.execute(
        "select cuenta,valor from usuario_eerr where cod_entidad='%s' and usuario='%s'" % (cod_entidad, id_user))
    resultado = cursor.fetchall()
    RESULTADO['Dias de Caja'].append(dict(resultado).get('Dias de Caja', float(RESULTADO['Dias de Caja'][-1]) * 0.8 + RESULTADO['Dias de Caja'][-2] * 0.2))
    # RESULTADO['Dias de Caja'].append(
    #     RESULTADO['Dias de Caja'][-1] * 0.8 + RESULTADO['Dias de Caja'][
    #         -2] * 0.2)
    RESULTADO['Dias De Cobro'].append(dict(resultado).get('Dias De Cobro', float(RESULTADO['Dias De Cobro'][-1]) * 0.8 +
                                                         RESULTADO['Dias De Cobro'][-2] * 0.2))
    # RESULTADO['Dias De Cobro'].append(
    #     RESULTADO['Dias De Cobro'][-1] * 0.8 + RESULTADO['Dias De Cobro'][
    #         -2] * 0.2)
    RESULTADO['Dias de Inventarios'].append(dict(resultado).get('Dias de Inventarios', float(RESULTADO['Dias de Inventarios'][-1]) * 0.8 +
                                                          RESULTADO['Dias de Inventarios'][-2] * 0.2))
    # RESULTADO['Dias de Inventarios'].append(
    #     RESULTADO['Dias de Inventarios'][-1] * 0.8 + RESULTADO['Dias de Inventarios'][
    #         -2] * 0.2)
    RESULTADO['Dias De Pago'].append(
        dict(resultado).get('Dias De Pago', float(RESULTADO['Dias De Pago'][-1]) * 0.8 +
                            RESULTADO['Dias De Pago'][-2] * 0.2))
    # RESULTADO['Dias De Pago'].append(
    #     RESULTADO['Dias De Pago'][-1] * 0.8 + RESULTADO['Dias De Pago'][
    #         -2] * 0.2)
    COLUMNAS.append("Proyección")
    return RESULTADO.values(), COLUMNAS


# funcion de estado resultado no ocupada
def get_eerr(cod_entidad, anio):
    cursor = cnx.cursor()
    aniom = int(anio) - 1
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades ordinarias'] = "(float(a.get(540,1)) - float(b.get(540,1)))/float(a.get(540,1)  if (a.get(540,0) and b.get(540,0)) else 0"
    RATIOS[
        'Prueba Acida'] = "(float(a.get(608,0)) - float(a.get(695,0))) / float(a.get(668,0)) if (a.get(608,0) and a.get(668,0) and a.get(695,0)) else 0"
    RATIOS[
        'Dias De Cobro'] = "(((float(a.get(775) or 0) / float(a.get(540) or 0)) * float(1.19)))* float(365) if (a.get(775,0) and a.get(540,0)) else 0"
    RATIOS[
        'Dias De Pago'] = "(float(a.get(783) or 0) / (-float(a.get(727) or 0) + float(a.get(695) or 0) - float(b.get(695) or 0)))*365 if (a.get(783,0) and a.get(727,0)and b.get(695,0)) else 0"
    RATIOS[
        'Dias De Existencia'] = "((float(a.get(695) or 0) / float(a.get(727) or 0)) * float(365)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'ROI'] = "(float(a.get(479) or 0) / float(a.get(808) or 0)*100) if (a.get(479,0) and a.get(808,0)) else 0"
    RATIOS[
        'ROE'] = "(float(a.get(479) or 0) / float(a.get(681) or 0)*100) if (a.get(479,0) and a.get(681,0)) else 0"
    RATIOS[
        'Leverage'] = "(float(a.get(519) or 0) / float(a.get(681) or 0)) if (a.get(519,0) and a.get(681,0)) else 0"
    RATIOS[
        'Corriente'] = "(float(a.get(668) or 0) / float(a.get(519) or 0)*100) if (a.get(668,0) and a.get(519,0)) else 0"
    RATIOS[
        'No Corriente'] = "(float(a[809] or 0) / float(a[519] or 0)*100) if (a.get(809,0) and a.get(519,0)) else 0"
    RATIOS[
        'Margen Neto'] = "(float(a.get(479) or 0) / float(a.get(540) or 0)*100) if (a.get(479,0) and a.get(540,0)) else 0"
    RATIOS[
        'Rotacion Activos'] = "(float(a.get(540) or 0) / float(a.get(808) or 0)) if (a.get(540,0) and a.get(808,0)) else 0"
    RATIOS[
        'Apalancamiento'] = "(float(a.get(808) or 0) / float(a.get(681) or 0)) if (a.get(808,0) and a.get(681,0)) else 0"
    RATIOS[
        'Dupont'] = "(((float(a.get(479) or 0) / float(a.get(540) or 0)) * (float(a.get(540) or 0) / float(a.get(808) or 0))) * (float(a.get(808) or 0) / float(a.get(681) or 0))*100)  if (a.get(479,0) and a.get(540,0)and a.get(808,0)and a.get(681,0)) else 0"
    RATIOS[
        'BPA'] = "(float(a.get(479) or 0) / float(a.get(685) or 0)) if (a.get(479,0) and a.get(685,0)) else 0"
    RATIOS[
        'Dias de Caja'] = "((float(a.get(739) or 0) / (float(a.get(540) or 1) - float(a.get(479)))) * 365) if (a.get(739,0) and a.get(540,0) and a.get(479)) else 0"
    RATIOS[
        'Ebitda'] = "(float(a.get(479) or 0) + float(a.get(764)or 0) + float(a.get(476)or 0) + float(a.get(832)or 0) + float(a.get(865)or 0)) if (a.get(479,0) and a.get(764,0) and a.get(476) and a.get(832) and a.get(865)) else 0"
    RATIOS[
        'Cobertura Interes'] = "((float(a.get(479) or 0) + float(a.get(764)) + float(a.get(476)) + float(a.get(832)) + float(a.get(865)))) / float(a.get(764) or 0) if (a.get(479,0) and a.get(764,0) and a.get(476) and a.get(832) and a.get(865)) else 0"
    RATIOS[
        'Rotacion De Inventarios'] = "(float(a.get(695) or 0) / float(a.get(727) or 0)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'Tasa Interes Promedio'] = "float(a.get(764) or 0) / (((float(a.get(582) or 0) + float(a.get(791) or 0) + float(b.get(582) or 0)+ float(b.get(791) or 0)))/2) if (a.get(764,0) and a.get(582,0)and a.get(791,0)  and b.get(582,0)and b.get(791,0)) else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from documento  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_documento INNER JOIN documento USING (cod_documento) where cod_entidad = '%s' and anio in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["RATIOS"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio))
        resumen = cursor.fetchall()

        COLUMNAS.insert(1, anio)
        a = dict()
        for r in resumen:
            a[r[1]] = r[3]
        for r in RATIOS:
            raux = RESULTADO.get(r, [r])
            raux.insert(1, eval(RATIOS[r]))
            RESULTADO[r] = raux
        b = a
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


# funcion extraccion ratios
def get_ratiosdd(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    aniom = int(anio) - 1
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS['Liquidez'] = "(float(a.get(608,1)) / float(a.get(668,1))) if (a.get(608,0) and a.get(668,0)) else 0"
    RATIOS[
        'Prueba Acida'] = "(float(a.get(608,0)) - float(a.get(695,0))) / float(a.get(668,0)) if (a.get(608,0) and a.get(668,0) and a.get(695,0)) else 0"
    RATIOS[
        'Dias De Cobro'] = "float(a.get(775) or 0) / (float(a.get(540) or 0) * float(1.19))* 365 if (a.get(775,0) and a.get(540,0)) else 0"
    RATIOS[
        'Dias De Pago'] = "((float(a.get(783) or 0)) / (float(a.get(727) or 0) + float(a.get(695) or 0) - float(b.get(695) or 0)))*365 if (a.get(783,0) and a.get(727,0)and b.get(695,0)) else 0"
    RATIOS[
        'Dias De Existencia'] = "((float(a.get(695) or 0) / float(a.get(727) or 0)) * float(365)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'ROI'] = "(float(a.get(479) or 0) / float(a.get(808) or 0)*100) if (a.get(479,0) and a.get(808,0)) else 0"
    RATIOS[
        'ROE'] = "(float(a.get(479) or 0) / float(a.get(681) or 0)*100) if (a.get(479,0) and a.get(681,0)) else 0"
    RATIOS[
        'Leverage'] = "(float(a.get(519) or 0) / float(a.get(681) or 0)) if (a.get(519,0) and a.get(681,0)) else 0"
    RATIOS[
        'Corriente'] = "(float(a.get(668) or 0) / float(a.get(519) or 0)*100) if (a.get(668,0) and a.get(519,0)) else 0"
    RATIOS[
        'No Corriente'] = "(float(a[809] or 0) / float(a[519] or 0)*100) if (a.get(809,0) and a.get(519,0)) else 0"
    RATIOS[
        'Margen Neto'] = "(float(a.get(479) or 0) / float(a.get(540) or 0)*100) if (a.get(479,0) and a.get(540,0)) else 0"
    RATIOS[
        'Rotacion Activos'] = "(float(a.get(540) or 0) / float(a.get(808) or 0)) if (a.get(540,0) and a.get(808,0)) else 0"
    RATIOS[
        'Apalancamiento'] = "(float(a.get(808) or 0) / float(a.get(681) or 0)) if (a.get(808,0) and a.get(681,0)) else 0"
    RATIOS[
        'Dupont'] = "(((float(a.get(479) or 0) / float(a.get(540) or 0)) * (float(a.get(540) or 0) / float(a.get(808) or 0))) * (float(a.get(808) or 0) / float(a.get(681) or 0))*100)  if (a.get(479,0) and a.get(540,0)and a.get(808,0)and a.get(681,0)) else 0"
    RATIOS[
        'BPA'] = "(float(a.get(479) or 0) / float(a.get(685) or 0)) if (a.get(479,0) and a.get(685,0)) else 0"
    RATIOS[
        'Dias de Caja'] = "((float(a.get(739) or 0) / (float(a.get(540) or 1) - float(a.get(479)))) * 365) if (a.get(739,0) and a.get(540,0) and a.get(479)) else 0"
    RATIOS[
        'Ebitda'] = "(float(a.get(479) or 0) + float(a.get(764)or 0) + float(a.get(476)or 0) + float(a.get(864)or 0)) if (a.get(479,0) and a.get(764,0) and a.get(476) and a.get(864)) else 0"
    RATIOS[
        'Cobertura Interes'] = "((float(a.get(479) or 0) + float(a.get(764)) + float(a.get(476)) + float(a.get(832)) + float(a.get(865)))) / float(a.get(764) or 0) if (a.get(479,0) and a.get(764,0) and a.get(476) and a.get(832) and a.get(865)) else 0"
    RATIOS[
        'Rotacion De Inventarios'] = "(float(a.get(695) or 0) / float(a.get(727) or 0)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'Tasa Interes Promedio'] = "float(a.get(764) or 0) / (((float(a.get(582) or 0) + float(a.get(791) or 0) + float(b.get(582) or 0)+ float(b.get(791) or 0)))/2) if (a.get(764,0) and a.get(582,0)and a.get(791,0)  and b.get(582,0)and b.get(791,0)) else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_documento  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_documento  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["RATIOS"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
            b = a

    return RESULTADO.values(), COLUMNAS


# implemenctacion ratios segun funcion asociada.
@app.route('/ratioLiquidez/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def ratioLiquidez(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    empresa = request.args.get("empresa")
    if request.args.get("mes"):
        mes = request.args.get("mes")
        if empresa != None:
            cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
            en = cursor.fetchone()[1]
            data1, columnas1 = get_ratiosdd(cod_entidad, anio, mes)
            return render_template("/ratioLiquidez2.html", entidad=entidad, data=list(data1),
                                   columnas1=columnas1,
                                   data1=list(data1), en=en, empresa=empresa, cod_entidad=cod_entidad)
        data1, columnas1 = get_ratiosdd(cod_entidad, anio, mes)
        return render_template("/ratioLiquidez2.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad, empresa=empresa)
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(cod_entidad, anio, mes)
        return render_template("/ratioLiquidez2.html", entidad=entidad, data=list(data1),
                               columnas1=columnas1,
                               data1=list(data1), en=en, empresa=empresa, cod_entidad=cod_entidad)
    data, columnas = get_ratiosdd(cod_entidad, anio, mes)
    return render_template("/ratioLiquidez2.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa,
                           cod_entidad=cod_entidad)


# comparación por empresa segun usuario lo requiera
@app.route('/comparatuempresa/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def comparatuempresa(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    empresa = request.args.get("empresa")
    if request.args.get("mes"):
        mes = request.args.get("mes")
        if empresa != None:
            cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
            en = cursor.fetchone()[1]
            data1, columnas1 = get_ratiosdd(cod_entidad, anio, mes)
            return render_template("/comparatuempresa.html", entidad=entidad, data=list(data1),
                                   columnas1=columnas1,
                                   data1=list(data1), en=en, empresa=empresa, cod_entidad=cod_entidad)
        data1, columnas1 = get_ratiosdd(cod_entidad, anio, mes)
        return render_template("/comparatuempresa.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad, empresa=empresa)
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(cod_entidad, anio, mes)
        return render_template("/comparatuempresa.html", entidad=entidad, data=list(data1),
                               columnas1=columnas1,
                               data1=list(data1), en=en, empresa=empresa, cod_entidad=cod_entidad)
    data, columnas = get_ratiosdd(cod_entidad, anio, mes)
    return render_template("/comparatuempresa.html", entidad=entidad, data=list(data), columnas=columnas,
                           empresa=empresa,
                           cod_entidad=cod_entidad)


# implementacion de analisis relativo
@app.route('/analisisRelativo/<cod_entidad>/<anio>', methods=["GET", "POST"])
def analisisRelativo(cod_entidad, anio):
    cursor = cnx.cursor()
    aniom = int(anio) - 1

    RATIOS = {}
    RATIOS[
        'Ingresos de Actividades'] = "(float(a.get(540,0)) / float(a.get(540,0))*100) if (a.get(540,0) and a.get(540,0)) else 0"
    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)) / float(a.get(540,1))*100) if (a.get(727,0) and a.get(540,0)) else 0"
    RATIOS[
        'Otros Ingresos'] = "(float(a.get(682,0)) / float(a.get(540,0))*100) if (a.get(682,0) and a.get(540,0)) else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,0)) / float(a.get(540,0))*100) if (a.get(1324,0) and a.get(540,0)) else 0"
    RATIOS[
        'Gastos Administracion'] = "(float(a.get(618,0)) / float(a.get(540,0))*100) if (a.get(618,0) and a.get(540,0)) else 0"
    RATIOS[
        'Otros Gastos'] = "(float(a.get(815,0)) / float(a.get(540,0))*100) if (a.get(815,0) and a.get(540,0)) else 0"
    RATIOS[
        'Otras Ganancias'] = "(float(a.get(1325,0)) / float(a.get(540,0))*100) if (a.get(1325,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias'] = "(float(a.get(817,0)) / float(a.get(540,0))*100) if (a.get(817,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Que Surgen'] = "(float(a.get(1326,0)) / float(a.get(540,0))*100) if (a.get(1326,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ingresos Financieros'] = "(float(a.get(558,0)) / float(a.get(540,0))*100) if (a.get(558,0) and a.get(540,0)) else 0"
    RATIOS[
        'Costos Financieros'] = "(float(a.get(764,0)) / float(a.get(540,0))*100) if (a.get(764,0) and a.get(540,0)) else 0"
    RATIOS[
        'Deterioro de Valor'] = "(float(a.get(9744,0)) / float(a.get(540,0))*100) if (a.get(9744,0) and a.get(540,0)) else 0"
    RATIOS[
        'Diferencias de Cambio'] = "(float(a.get(849,0)) / float(a.get(540,0))*100) if (a.get(849,0) and a.get(540,0)) else 0"
    RATIOS[
        'Resultados por Unidades'] = "(float(a.get(516,0)) / float(a.get(540,0))*100) if (a.get(516,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias de Cobertura'] = "(float(a.get(10377,0)) / float(a.get(540,0))*100) if (a.get(10377,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Antes del Impuesto'] = "(float(a.get(788,0)) / float(a.get(540,0))*100) if (a.get(788,0) and a.get(540,0)) else 0"
    RATIOS[
        'Gastos por Impuestos a las Ganancias'] = "(float(a.get(476,0)) / float(a.get(540,0))*100) if (a.get(476,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Procedentes Continuada'] = "(float(a.get(774,0)) / float(a.get(540,0))*100) if (a.get(774,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancias Porcentes Discontinuas'] = "(float(a.get(1328,0)) / float(a.get(540,0))*100) if (a.get(1328,0) and a.get(540,0)) else 0"
    RATIOS[
        'Ganancia (Perdida)'] = "(float(a.get(479,0)) / float(a.get(540,0))*100) if (a.get(479,0) and a.get(540,0)) else 0"

    cursor.execute(
        """SELECT DISTINCT
* from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    SQL_RESUMEN = """select distinct *  from resumen_documento  where cod_entidad = '%s' and anio in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["RATIOS"]
    while existan_datos:
        COLUMNAS.append(anio)
        a = dict()
        for r in resumen:
            a[r[4]] = r[9]
        for r in RATIOS:
            RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
        anio = int(anio) - 1
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio))
        resumen = cursor.fetchall()
        existan_datos = resumen != []
    return render_template("/analisisRelativo.html", entidad=entidad, data=list(RESULTADO.values()),
                           columnas=COLUMNAS, cod_entidad=cod_entidad)


# funcion para sacar el resumen del reporte NOF-FM
def get_nofresumen(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'NOF'] = "(float(a.get(608,1))- float(a.get(668,1)) + float(a.get(582,1)))  if  (a.get(608,0)) and  (a.get(668,0)) and (a.get(582,0))  else 0"
    RATIOS[
        'FM'] = "(float(a.get(681,1))+ float(a.get(668,1)) + float(a.get(809,1)))  if  (a.get(809,0)) and  (a.get(681,0)) and (a.get(668,0))  else 0"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from nof_resumen  where cod_entidad = '%s' and anio >= '2015' and mes='12'"""
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad))
    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from nof_resumen  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))

    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["NOF"]
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    return RESULTADO.values(), COLUMNAS


# funcion de vetnas por trimetre ene el resumen
def get_ventasxtrimestreresumen(cod_entidad, anio):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ventas por Trimestre'] = "(float(a.get(540,1)))  if  (a.get(540,0))  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from ventasxtrimestre_resumen  where cod_entidad = '%s' and anio > '2016'"""
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad))
    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from ventasxtrimestre_resumen  where cod_entidad = '%s' and anio in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["VENTAS"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio))
        resumen = cursor.fetchall()
        a = dict()
        coun = 0
        for r in resumen:
            a[r[4]] = r[9]
            COLUMNAS.insert(1, resumen[coun][1])
            coun += 1
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
        b = a

    return RESULTADO.values(), COLUMNAS


# funcion de portada ratios
def get_portadaratiosdd(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    aniom = int(anio) - 1
    # DEFINICION DE RATIOS
    RATIOS = {}

    RATIOS[
        'Dias De Cobro'] = "float(a.get(775) or 0) / (float(a.get(540) or 0) * float(1.19))* 365 if (a.get(775,0) and a.get(540,0)) else 0"
    RATIOS[
        'Dias De Pago'] = "((float(a.get(783) or 0)) / (float(a.get(727) or 0) + float(a.get(695) or 0) - float(b.get(695) or 0)))*365 if (a.get(783,0) and a.get(727,0)and b.get(695,0)) else 0"
    RATIOS[
        'Dias De Existencia'] = "((float(a.get(695) or 0) / float(a.get(727) or 0)) * float(365)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'ROI'] = "(float(a.get(479) or 0) / float(a.get(808) or 0)*100) if (a.get(479,0) and a.get(808,0)) else 0"
    RATIOS[
        'ROE'] = "(float(a.get(479) or 0) / float(a.get(681) or 0)*100) if (a.get(479,0) and a.get(681,0)) else 0"

    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_portadaratios  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_portadaratios  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["RATIOS"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


# funcion de portada etado resultado
def get_portadaeresultado(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos'] = "(float(a.get(540,1)),(float(a.get(540,1))/float(a.get(540,1)))*100  if  (a.get(540,0))  else 0)"
    RATIOS[
        'Margen Bruto'] = "(float(a.get(805,1)),(float(a.get(805,1))/float(a.get(540,1)))*100  if  (a.get(805,0))  else 0)"
    RATIOS[
        'GAV + Distribucion'] = "(float(a.get(1324,1)),(float(a.get(1324,1))+float(a.get(618,1)))/3  if  (a.get(1324,0))  else 0)"
    RATIOS[
        'Financieros'] = "(float(a.get(764,1)),(float(a.get(764,1))/float(a.get(540,1)))*100  if  (a.get(764,0))  else 0)"
    RATIOS[
        'Resultado'] = "(float(a.get(479,1)),(float(a.get(479,1))/float(a.get(540,1)))*100  if  (a.get(479,0))  else 0)"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_portadaeerr  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_portadaeerr  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["ESTADO RESULTADO"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


def get_portadaratiosddindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    aniom = int(anio) - 1
    # DEFINICION DE RATIOS
    RATIOS = {}

    RATIOS[
        'Dias De Cobro'] = "float(a.get(775) or 0) / (float(a.get(540) or 0) * float(1.19))* 365 if (a.get(775,0) and a.get(540,0)) else 0"
    RATIOS[
        'Dias De Pago'] = "((float(a.get(783) or 0)) / (float(a.get(727) or 0) + float(a.get(695) or 0) - float(b.get(695) or 0)))*365 if (a.get(783,0) and a.get(727,0)and b.get(695,0)) else 0"
    RATIOS[
        'Dias De Existencia'] = "((float(a.get(695) or 0) / float(a.get(727) or 0)) * float(365)) if (a.get(695,0) and a.get(727,0)) else 0"
    RATIOS[
        'ROI'] = "(float(a.get(479) or 0) / float(a.get(808) or 0)*100) if (a.get(479,0) and a.get(808,0)) else 0"
    RATIOS[
        'ROE'] = "(float(a.get(479) or 0) / float(a.get(681) or 0)*100) if (a.get(479,0) and a.get(681,0)) else 0"

    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_portadaratiosindustria  where cod_industria = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_industria ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_portadaratiosindustria  where cod_industria = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["RATIOS"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][2])
            a = dict()
            for r in resumen:
                a[r[5]] = r[10]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


def get_portadaeresultadoindustria(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ingresos'] = "(float(a.get(540,1)),(float(a.get(540,1))/float(a.get(540,1)))*100  if  (a.get(540,0))  else 0)"
    RATIOS[
        'Margen Bruto'] = "(float(a.get(805,1)),(float(a.get(805,1))/float(a.get(540,1)))*100  if  (a.get(805,0))  else 0)"
    RATIOS[
        'GAV + Distribucion'] = "(float(a.get(1324,1)),(float(a.get(1324,1))+float(a.get(618,1)))/3  if  (a.get(1324,0))  else 0)"
    RATIOS[
        'Financieros'] = "(float(a.get(764,1)),(float(a.get(764,1))/float(a.get(540,1)))*100  if  (a.get(764,0))  else 0)"
    RATIOS[
        'Resultado'] = "(float(a.get(479,1)),(float(a.get(479,1))/float(a.get(540,1)))*100  if  (a.get(479,0))  else 0)"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_portadaeerrindustrias  where cod_industria = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_industria ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_portadaeerrindustrias  where cod_industria = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["ESTADO RESULTADO"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][2])
            a = dict()
            for r in resumen:
                a[r[5]] = r[10]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    return RESULTADO.values(), COLUMNAS


# funcion de graficos estado de resultado (no implementado)
def get_portadagraficoeerr(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}

    RATIOS[
        'Costos de Ventas'] = "(float(a.get(727,1)))  if  a.get(727,0)  else 0"
    RATIOS[
        'Costos de Distribucion'] = "(float(a.get(1324,1)))  if  a.get(1324,0)  else 0"
    RATIOS[
        'Gastos de administración'] = "(float(a.get(618,1)))  if  a.get(618,0)  else 0"
    RATIOS[
        'Costos financieros'] = "(float(a.get(764,1)))  if  a.get(764,0)  else 0"
    RATIOS[
        'Ganancia (pérdida)'] = "(float(a.get(479,1)))  if  a.get(479,0)  else 0"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from documento  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_proyeccioneerr  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["ESTADO RESULTADO"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        COLUMNAS.insert(1, resumen[0][1])
        a = dict()
        for r in resumen:
            a[r[4]] = r[9]
        for r in RATIOS:
            raux = RESULTADO.get(r, [r])
            raux.insert(1, eval(RATIOS[r]))
            RESULTADO[r] = raux
        b = a
    return RESULTADO.values(), COLUMNAS


# función de fiananciamiento.
def get_Financiamiento(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}

    RATIOS[
        'Deuda'] = "(float(a.get(582,1))+float(a.get(791,1)))  if  (a.get(582,0) and a.get(791,0))  else 0"
    RATIOS[
        'Capital'] = "(float(a.get(681,1)))  if  a.get(681,0)  else 0"
    RATIOS[
        'Total'] = "(float(a.get(582,1))+float(a.get(791,1))+float(a.get(681,1)))  if  (a.get(582,0) and a.get(791,0)and a.get(681,0)) else 0"
    RATIOS[
        '%Deuda'] = "((float(a.get(582,1))+float(a.get(791,1)))/(float(a.get(582,1))+float(a.get(791,1))+float(a.get(681,1)))*100)  if  (a.get(582,0) and a.get(791,0)and a.get(681,0)) else 0"
    RATIOS[
        '%Capital'] = "((float(a.get(681,1)))/(float(a.get(582,1))+float(a.get(791,1))+float(a.get(681,1)))*100)  if  (a.get(582,0) and a.get(791,0)and a.get(681,0)) else 0"
    RATIOS[
        'Tasa Interes'] = "float(a.get(764) or 0) / (((float(a.get(582) or 0) + float(a.get(791) or 0) + float(b.get(582) or 0)+ float(b.get(791) or 0)))/2) if (a.get(764,0) and a.get(582,0)and a.get(791,0)  and b.get(582,0)and b.get(791,0)) else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_EstructuraFinanciamiento  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_EstructuraFinanciamiento  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["Financiamiento"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
            b = a
    return RESULTADO.values(), COLUMNAS


@app.route('/EstructuraFinanciamiento/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def EstructuraFinanciamiento(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        data1, columnas1 = get_Financiamiento(cod_entidad, anio, mes)

        return render_template("/EstructuraFinanciamiento.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad)
    data, columnas = get_Financiamiento(cod_entidad, anio, mes)

    empresa = request.args.get("empresa")
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(empresa, anio)
        return render_template("/EstructuraFinanciamiento.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data1), columnas1=columnas1, en=en, empresa=empresa)
    return render_template("/EstructuraFinanciamiento.html", entidad=entidad, data=list(data), columnas=columnas,
                           empresa=empresa, cod_entidad=cod_entidad)


@app.route('/ResumenEmpresa/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def ResumenEmpresa(cod_entidad, anio, mes):
    if session.get("username"):
        cursor = cnx.cursor()
        parametros = {'cod_entidad': cod_entidad}
        cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""",
                       parametros)
        rest = cursor.fetchone()
        if not rest:
            abort(404)
        entidad = rest[1]
        cursor.execute("""SELECT
                    public.entidad.cod_entidad,
                    public.entidad.desc_entidad,
                    public.documento.desc_documento,
                    public.documento.anio,
                    public.documento.mes,
                    public.documento.cod_documento,
                    public.documento.hash
                    FROM
                    public.documento
                    INNER JOIN public.entidad ON public.documento.cod_entidad = public.entidad.cod_entidad
                    WHERE documento.cod_entidad = '%s'""" % (cod_entidad))
        entidadC = cursor.fetchall()
        # NOF-FM
        data, columnas = get_nofresumen(cod_entidad, anio, mes)
        columna = columnas[1:]
        if columna == []:
            columna = "n/a"
        else:
            columna = columnas[1:]

        if list(data) == []:
            datonof = "n/a"
            dato2nof = "n/a"
        else:
            datonof = list(data)[0][1:]
            dato2nof = list(data)[1][1:]
        # VENTASXTRIMESTRE
        data1, columnas1 = get_ventasxtrimestreresumen(cod_entidad, anio)
        columna1 = columnas1[1:]
        if columna1 == []:
            columna1 = "n/a"
        else:
            columna1 = columnas1[1:]

        if list(data1) == []:
            datonvxt1 = "n/a"
        else:
            datonvxt1 = list(data1)[0][1:]

        # BALANCE
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='608'""" % (cod_entidad))
        corriente = cursor.fetchall()
        if corriente:
            corriente = corriente
        else:
            corriente = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='825'""" % (cod_entidad))
        Nocorriente = cursor.fetchall()
        if Nocorriente:
            Nocorriente = Nocorriente
        else:
            Nocorriente = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='808' ORDER BY anio""" % (
                cod_entidad))
        Total = cursor.fetchall()
        if Total:
            Total = Total
        else:
            Total = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='668'""" % (cod_entidad))
        corrientepasivo = cursor.fetchall()
        CLP = 'N/A'
        USD = 'N/A'
        if corrientepasivo:
            if corrientepasivo[0][10] == 'CLP':
                CLP = corrientepasivo[0][10]
                USD = 'none'
            else:
                USD = corrientepasivo[0][10]
                CLP = 'none'
            corrientepasivo = corrientepasivo
        else:
            corrientepasivo = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='809'""" % (cod_entidad))
        nocorrientepasivo = cursor.fetchall()
        if nocorrientepasivo:
            nocorrientepasivo = nocorrientepasivo
        else:
            nocorrientepasivo = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='681'""" % (cod_entidad))
        patrimonio = cursor.fetchall()
        if patrimonio:
            patrimonio = patrimonio
        else:
            patrimonio = "n/a"
        cursor.execute(
            """select * from resumen_PortadaBalance where cod_entidad = '%s' and cod_cuenta='754' ORDER BY anio""" % (
                cod_entidad))
        totalpasivo = cursor.fetchall()
        if totalpasivo:
            totalpasivo = totalpasivo
        else:
            totalpasivo = "n/a"
        cursor.execute(
            """select * from resumen_PortadaEstructuraFinanciamiento where cod_entidad = '%s' and cod_cuenta='582'""" % (
                cod_entidad))
        rest = cursor.fetchone()
        if rest:
            D1 = rest[9]
        else:
            D1 = 1
        cursor.execute(
            """select * from resumen_PortadaEstructuraFinanciamiento where cod_entidad = '%s' and cod_cuenta='791' """ % (
                cod_entidad))
        rest = cursor.fetchone()
        if rest:
            D2 = rest[9]
        else:
            D2 = 1
        if D1 == 1 or D2 == 1:
            Deudor = "n/a"
        else:
            Deudor = (D1 + D2)
        cursor.execute(
            """select * from resumen_PortadaEstructuraFinanciamiento where cod_entidad = '%s' and cod_cuenta='681'""" % (
                cod_entidad))
        rest = cursor.fetchone()
        if rest:
            Capital = rest[9]
        else:
            Capital = "n/a"
        if Capital == "n/a" or Deudor == "n/a":
            porcientodeuda = "n/a"
            porcientoCapital = "n/a"
            testructura = "n/a"
        else:
            testructura = (Deudor + Capital)
            porcientodeuda = (Deudor / testructura) * 100
            porcientoCapital = (Capital / testructura) * 100
        # RATIOS
        data3, columnas3 = get_portadaratiosdd(cod_entidad, anio, mes)
        # EERR
        data4, columnas4 = get_portadaeresultado(cod_entidad, anio, mes)
        # GRAFICO EERR
        return render_template("/ResumenEmpresa.html", entidad=entidad, data=list(data), columnas=columnas,
                               columna1=columna1, datonvxt1=datonvxt1,
                               columna=columna, datonof=datonof, dato2nof=dato2nof, data1=list(data1),
                               columnas1=columnas1, corriente=corriente, Nocorriente=Nocorriente, Total=Total,
                               corrientepasivo=corrientepasivo, nocorrientepasivo=nocorrientepasivo,
                               totalpasivo=totalpasivo, Deudor=Deudor, Capital=Capital, testructura=testructura,
                               porcientodeuda=porcientodeuda, porcientoCapital=porcientoCapital, data3=data3,
                               columnas3=columnas3, data4=list(data4), columnas4=columnas4, entidadC=entidadC,
                               patrimonio=patrimonio, USD=USD, CLP=CLP)
    return redirect("/login")


def get_nof(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'NOF'] = "(float(a.get(608,1))- float(a.get(668,1)) + float(a.get(582,1)))  if  (a.get(608,0)) and  (a.get(668,0)) and (a.get(582,0))  else 0"
    RATIOS[
        'FM'] = "(float(a.get(681,1))+ float(a.get(668,1)) + float(a.get(809,1)))  if  (a.get(809,0)) and  (a.get(681,0)) and (a.get(668,0))  else 0"
    RATIOS[
        'NOF-FM'] = "((float(a.get(608,1))- float(a.get(668,1)) + float(a.get(582,1)))-(float(a.get(681,1))+ float(a.get(668,1)) + float(a.get(809,1)))) if  (a.get(608,0)) and  (a.get(668,0)) and (a.get(582,0)) and (a.get(809,0)) and  (a.get(681,0))  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from nof  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from nof  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["NOF"]
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


@app.route('/nof/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def nof(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    empresa = request.args.get("empresa")
    data, columnas = get_nof(cod_entidad, anio, mes)
    if request.args.get("mes"):
        mes = request.args.get("mes")
        columna = columnas[1:]
        dato = CMon(list(data)[0][1:])
        dato2 = list(data)[1][1:]
        data, columnas = get_nof(cod_entidad, anio, mes)
        return render_template("/nof.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa,
                               columna=columna, dato=dato, dato2=dato2, cod_entidad=cod_entidad)
    # app_json = json.dumps(resultado)
    # print(app_json)
    columna = columnas[1:]
    dato = CMon(list(data)[0][1:])
    dato2 = list(data)[1][1:]
    empresa = request.args.get("empresa")
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(empresa, anio)
        return render_template("/nof.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data1), columnas1=columnas1, en=en, empresa=empresa)
    return render_template("/nof.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa,
                           columna=columna, dato=dato, dato2=dato2, cod_entidad=cod_entidad)


def get_ventasxtrimestre(cod_entidad, anio):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Ventas por Trimestre'] = "(float(a.get(540,1)))  if  (a.get(540,0))  else 0"
    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_ventasxtrimestre  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_ventasxtrimestre  where cod_entidad = '%s' and anio in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["VENTAS"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio))
        resumen = cursor.fetchall()
        a = dict()
        coun = 0
        for r in resumen:
            a[r[4]] = r[9]
            COLUMNAS.insert(1, resumen[coun][1])
            coun += 1
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
        b = a

    return RESULTADO.values(), COLUMNAS


@app.route('/ventasxtrimestre/<cod_entidad>/<anio>', methods=["GET", "POST"])
def ventasxtrimestre(cod_entidad, anio):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    data, columnas = get_ventasxtrimestre(cod_entidad, anio)
    empresa = request.args.get("empresa")
    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(empresa, anio)
        return render_template("/ventasxtrimestre.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data1), columnas1=columnas1, en=en, empresa=empresa)
    return render_template("/ventasxtrimestre.html", entidad=entidad, data=list(data), columnas=columnas,
                           empresa=empresa, cod_entidad=cod_entidad)


@app.route('/balance1/<cod_documento>/<cod_role>', methods=["GET", "POST"])
def balance1(cod_documento, cod_role):
    cursor = cnx.cursor()
    cursor.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, case when not decimales isnull then desc_detalle_documento::numeric / 10 ^ abs(decimales) else 0 end valor
                        from detalle_documento
                        join cuenta using (cod_cuenta)
                        left join role_cuenta using (cod_cuenta)
                        left join role using(cod_role)
                        left join unidad using (cod_unidad)
                        join tipo_cuenta using (cod_tipo_cuenta)
                        join contexto using (cod_contexto)
                        join entidad using (cod_entidad)
                        join periodo using (cod_periodo)
                        left join context_escenarios using (cod_contexto)
                        left join escenario using (cod_escenario)
                        left join dimension using (cod_dimension)
                        --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
                        where cod_dimension is null  and cod_documento = %s and cod_role =%s and desc_unidad != '%s'
                        order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role, 'shares'))
    data = dictfetchall(cursor)
    cursor.execute("""select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, case when not decimales isnull then desc_detalle_documento::numeric / 10 ^ abs(decimales) else 0 end valor
                            from detalle_documento
                            join cuenta using (cod_cuenta)
                            left join role_cuenta using (cod_cuenta)
                            left join role using(cod_role)
                            left join unidad using (cod_unidad)
                            join tipo_cuenta using (cod_tipo_cuenta)
                            join contexto using (cod_contexto)
                            join entidad using (cod_entidad)
                            join periodo using (cod_periodo)
                            left join context_escenarios using (cod_contexto)
                            left join escenario using (cod_escenario)
                            left join dimension using (cod_dimension)
                            --where cod_periodo = 44 and cod_tipo_cuenta in (6,7)
                            where cod_dimension is null  and cod_documento = %s and cod_role =%s
                            order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role))
    date = cursor.fetchall()
    cursor.execute("""select distinct desc_periodo
                           from detalle_documento
                           join cuenta using (cod_cuenta)
                           left join role_cuenta using (cod_cuenta)
                           left join role using(cod_role)
                           join contexto using (cod_contexto)
                           join periodo using (cod_periodo)
                           left join context_escenarios using (cod_contexto)
                           left join escenario using (cod_escenario)
                           left join dimension using (cod_dimension)
                           where cod_dimension is null  and cod_documento = %s and cod_role =%s
                           order by desc_periodo desc""" % (cod_documento, cod_role))
    per = dictfetchall(cursor)
    for d in date:
        cod_rol = d[1]
        desc_role = d[0]
        entidad = d[13]
        cuenta = d[5]
        dineros = d[8]
        fechas = d[7]
    hoy = datetime.now()
    hoy = hoy.strftime("%Y-%m-%d")
    report = PdfCustomDetail(filename="%s.pdf" % (cod_rol), title=["%s" % (desc_role), entidad.__str__(), cuenta],
                             logo=getattr(sys, 'logo', 'xeeffy_logo_index.png'))
    pvt_kms = pivot(data, ('cod_role_cuenta', 'desc_cuenta'), ('desc_periodo',), 'valor')
    datas = []
    columnas = ["CUENTA"]
    data_linea = ['']
    ancho_total = 0
    colsWidth = [0]
    colAlign = ['LEFT']
    colType = ['str']
    for p in per:
        columnas.append(p['desc_periodo'])
        data_linea.append(0.0)
        colsWidth.append(60)
        ancho_total += 60
        colAlign.append("RIGHT")
        colType.append("str")
    colsWidth[0] = 540 - ancho_total
    for f in pvt_kms:
        dl = (list(f.get(('cod_role_cuenta', 'desc_cuenta'), [''])))
        for p in per:
            dl.append(CMon(f.get((p['desc_periodo'],), 0)))
        datas.append(dl)
    data_final = []
    datas.sort()
    for d in datas:
        data_final.append(d[1:])
    return render_template("/balance1.html", d=data_final, columnas=columnas, entidad=entidad, desc_role=desc_role,
                           hoy=hoy)


def get_balance(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    # DEFINICION DE RATIOS
    RATIOS = {}
    RATIOS[
        'Efectivo y equivalentes al efectivo'] = "(float(a.get(739,1)))  if  (a.get(739,0))  else 0"
    RATIOS[
        'Otros activos financieros corrientes'] = "(float(a.get(607,1)))  if  a.get(607,0)  else 0"
    RATIOS[
        'Otros activos no financieros corrientes'] = "(float(a.get(835,1)))  if  a.get(835,0)  else 0"
    RATIOS[
        'Deudores comerciales y otras cuentas por cobrar corrientes'] = "(float(a.get(775,1)))  if  a.get(775,0)  else 0"
    RATIOS[
        'Cuentas por cobrar a entidades relacionadas, corrientes'] = "(float(a.get(787,1)))  if  a.get(787,0)  else 0"
    RATIOS[
        'Inventarios corrientes'] = "(float(a.get(695,1)))  if  a.get(695,0)  else 0"
    RATIOS[
        'Activos biológicos corrientes'] = "(float(a.get(1290,1)))  if  a.get(1290,0)  else 0"
    RATIOS[
        'Activos por impuestos corrientes, corrientes'] = "(float(a.get(481,1)))  if  a.get(481,0)  else 0"
    RATIOS[
        'Total de activos corrientes distintos de los activo o grupos de activos'] = "(float(a.get(797,1)))  if  a.get(797,0)  else 0"
    RATIOS[
        'Activos no corrientes o grupos de activos para su disposición clasificados'] = "(float(a.get(1291,1)))  if  a.get(1291,0)  else 0"
    RATIOS[
        'Activos corrientes totales'] = "(float(a.get(608,1)))  if  a.get(608,0)  else 0"
    RATIOS[
        'Otros activos financieros no corrientes'] = "(float(a.get(520,1)))  if  a.get(520,0)  else 0"
    RATIOS[
        'Otros activos no financieros no corrientes'] = "(float(a.get(462,1)))  if  a.get(462,0)  else 0"
    RATIOS[
        'Cuentas por cobrar no corrientes'] = "(float(a.get(753,1)))  if  a.get(753,0)  else 0"
    RATIOS[
        'Cuentas por cobrar a entidades relacionadas, no corrientes'] = "(float(a.get(680,1)))  if  a.get(680,0)  else 0"
    RATIOS[
        'Inversiones contabilizadas utilizando el método de la participación'] = "(float(a.get(713,1)))  if  a.get(713,0)  else 0"
    RATIOS[
        'Activos intangibles distintos de la plusvalía'] = "(float(a.get(748,1)))  if  a.get(748,0)  else 0"
    RATIOS[
        'Plusvalía'] = "(float(a.get(866,1)))  if  a.get(866,0)  else 0"
    RATIOS[
        'Propiedades, planta y equipo'] = "(float(a.get(456,1)))  if  a.get(456,0)  else 0"
    RATIOS[
        'Activos biológicos no corrientes'] = "(float(a.get(1294,1)))  if  a.get(1294,0)  else 0"
    RATIOS[
        'Propiedad de inversión'] = "(float(a.get(581,1)))  if  a.get(581,0)  else 0"
    RATIOS[
        'Activos por impuestos diferidos'] = "(float(a.get(622,1)))  if  a.get(622,0)  else 0"
    RATIOS[
        'Total de activos no corrientes'] = "(float(a.get(825,1)))  if  a.get(825,0)  else 0"
    RATIOS[
        'Total de activos'] = "(float(a.get(808,1)))  if  a.get(808,0)  else 0"
    RATIOS[
        'Otros pasivos financieros corrientes'] = "(float(a.get(582,1)))  if  a.get(582,0)  else 0"
    RATIOS[
        'Cuentas por pagar comerciales y otras cuentas por pagar'] = "(float(a.get(783,1)))  if  a.get(783,0)  else 0"
    RATIOS[
        'Cuentas por pagar a entidades relacionadas, corrientes'] = "(float(a.get(461,1)))  if  a.get(461,0)  else 0"
    RATIOS[
        'Otras provisiones a corto plazo'] = "(float(a.get(659,1)))  if  a.get(659,0)  else 0"
    RATIOS[
        'Pasivos por impuestos corrientes, corrientes'] = "(float(a.get(477,1)))  if  a.get(477,0)  else 0"
    RATIOS[
        'Provisiones corrientes por beneficios a los empleados'] = "(float(a.get(756,1)))  if  a.get(756,0)  else 0"
    RATIOS[
        'Otros pasivos no financieros corrientes'] = "(float(a.get(621,1)))  if  a.get(621,0)  else 0"
    RATIOS[
        'Total de pasivos corrientes distintos de los pasivos incluidos'] = "(float(a.get(745,1)))  if  a.get(745,0)  else 0"
    RATIOS[
        'Pasivos corrientes totales'] = "(float(a.get(668,1)))  if  a.get(688,0)  else 0"
    RATIOS[
        'Otros pasivos financieros no corrientes'] = "(float(a.get(791,1)))  if  a.get(791,0)  else 0"
    RATIOS[
        'Cuentas por pagar no corrientes'] = "(float(a.get(822,1)))  if  a.get(822,0)  else 0"
    RATIOS[
        'Cuentas por pagar a entidades relacionadas, no corrientes'] = "(float(a.get(486,1)))  if  a.get(486,0)  else 0"
    RATIOS[
        'Otras provisiones a largo plazo'] = "(float(a.get(524,1)))  if  a.get(524,0)  else 0"
    RATIOS[
        'Pasivo por impuestos diferidos'] = "(float(a.get(640,1)))  if  a.get(640,0)  else 0"
    RATIOS[
        'Provisiones no corrientes por beneficios a los empleados'] = "(float(a.get(629,1)))  if  a.get(629,0)  else 0"
    RATIOS[
        'Otros pasivos no financieros no corrientes'] = "(float(a.get(633,1)))  if  a.get(633,0)  else 0"
    RATIOS[
        'Total de pasivos no corrientes'] = "(float(a.get(809,1)))  if  a.get(809,0)  else 0"
    RATIOS[
        'Total de pasivos'] = "(float(a.get(519,1)))  if  a.get(519,0)  else 0"
    RATIOS[
        'Capital emitido'] = "(float(a.get(859,1)))  if  a.get(859,0)  else 0"
    RATIOS[
        'Ganancias (pérdidas) acumuladas'] = "(float(a.get(670,1)))  if  a.get(670,0)  else 0"
    RATIOS[
        'Prima de emisión'] = "(float(a.get(939,1)))  if  a.get(939,0)  else 0"
    RATIOS[
        'Acciones propias en cartera'] = "(float(a.get(1303,1)))  if  a.get(1303,0)  else 0"
    RATIOS[
        'Otras participaciones en el patrimonio'] = "(float(a.get(1304,1)))  if  a.get(1304,0)  else 0"
    RATIOS[
        'Otras reservas'] = "(float(a.get(789,1)))  if  a.get(789,0)  else 0"
    RATIOS[
        'Patrimonio atribuible a los propietarios de la controladora'] = "(float(a.get(879,1)))  if  a.get(879,0)  else 0"
    RATIOS[
        'Participaciones no controladoras'] = "(float(a.get(620,1)))  if  a.get(620,0)  else 0"
    RATIOS[
        'Patrimonio total'] = "(float(a.get(681,1)))  if  a.get(681,0)  else 0"
    RATIOS[
        'Total de patrimonio y pasivos'] = "(float(a.get(754,1)))  if  a.get(754,0)  else 0"

    # AÑOS
    SQL_ANIOS = """select coalesce(min(anio),%s), coalesce(max(anio),%s)  from resumen_proyeccionesbalance  where cod_entidad = '%s' and anio <= %s """
    anios = {}
    cursor.execute(
        SQL_ANIOS % (anio, anio, cod_entidad, anio))

    anios = cursor.fetchone()
    anio = anios[0]
    # ENTIDAD
    cursor.execute(
        """SELECT DISTINCT
    * from entidad where cod_entidad ='%s'""" % (
            cod_entidad))
    entidad = cursor.fetchone()[1]
    # FIN ENTIDAD
    SQL_RESUMEN = """select distinct *  from resumen_proyeccionesbalance  where cod_entidad = '%s' and anio in ('%s') and mes in ('%s')"""
    RESULTADO = {}
    cursor.execute(
        SQL_RESUMEN % (cod_entidad, anio, mes))
    resumen = cursor.fetchall()
    existan_datos = resumen != []
    COLUMNAS = ["BALANCE"]
    b = dict()
    for anio in range(anios[0], anios[1] + 1):
        cursor.execute(
            SQL_RESUMEN % (cod_entidad, anio, mes))
        resumen = cursor.fetchall()
        if resumen:
            COLUMNAS.insert(1, resumen[0][1])
            a = dict()
            for r in resumen:
                a[r[4]] = r[9]
            for r in RATIOS:
                raux = RESULTADO.get(r, [r])
                raux.insert(1, eval(RATIOS[r]))
                RESULTADO[r] = raux
        b = a
    # while existan_datos:
    #     COLUMNAS.append(anio)
    #     a = dict()
    #     for r in resumen:
    #         a[r[1]] = r[3]
    #     for r in RATIOS:
    #         RESULTADO[r] = RESULTADO.get(r, [r]) + [eval(RATIOS[r])]
    #     anio = int(anio) - 1
    #     cursor.execute(
    #         SQL_RESUMEN % (cod_entidad, anio))
    #     resumen = cursor.fetchall()
    #     existan_datos = resumen != []
    return RESULTADO.values(), COLUMNAS


@app.route('/balance/<cod_entidad>/<anio>/<mes>', methods=["GET", "POST"])
def balance(cod_entidad, anio, mes):
    cursor = cnx.cursor()
    parametros = {'cod_entidad': cod_entidad}
    cursor.execute("""select cod_entidad,desc_entidad from entidad where cod_entidad =%(cod_entidad)s""", parametros)
    rest = cursor.fetchone()
    if not rest:
        abort(404)
    entidad = rest[1]
    if request.args.get("mes"):
        mes = request.args.get("mes")
        data1, columnas1 = get_balance(cod_entidad, anio, mes)
        return render_template("/balance.html", entidad=entidad, data=list(data1),
                               columnas=columnas1,
                               data1=list(data1), columnas1=columnas1, cod_entidad=cod_entidad)
    data, columnas = get_balance(cod_entidad, anio, mes)
    empresa = request.args.get("empresa")

    if empresa != None:
        cursor.execute("""select * from entidad where cod_entidad='%s'""" % (empresa))
        en = cursor.fetchone()[1]
        data1, columnas1 = get_ratiosdd(empresa, anio)
        return render_template("/balance.html", entidad=entidad, data=list(data),
                               columnas=columnas,
                               data1=list(data1), columnas1=columnas1, en=en, empresa=empresa)
    return render_template("/balance.html", entidad=entidad, data=list(data), columnas=columnas, empresa=empresa,
                           mes=mes, cod_entidad=cod_entidad)

    # funciones de ordenado y calculos de cada uno de los servicios


def JsonAgg(json, valores, claves, funcs=None):
    aggby = claves
    vals = valores
    js = json
    result = {}
    jresult = []
    nVals = len(valores)
    if funcs == None:
        funcs = len(valores) * ["sum"]
    for d in js:
        k = tuple([(i, d[i]) for i in aggby])
        result[k] = result.get(k, {})
        for idxv in range(nVals):
            va = vals[idxv]
            result[k][va] = result[k].get(va, 0)
            if funcs[idxv] == 'sum':
                result[k][va] += d.get(va)
            elif funcs[idxv] == 'count':
                result[k][va] += 1
            elif funcs[idxv] == 'max':
                if d.get(va) > result[k][va]:
                    result[k][va] = d.get(va)
            elif funcs[idxv] == 'min':
                if d.get(va) < result[k][va]:
                    result[k][va] = d.get(va)
    for r in result:
        jresult.append(dict(dict(r), **result[r]))
    del result
    return jresult


def CRut(rut):
    if rut == "":
        return rut
    rut = str.replace(rut, ".", "")
    rut = str.replace(rut, "-", "")
    rut = "0000000000" + rut
    l = len(rut)
    rut_aux = "-" + rut[l - 1:l]
    l = l - 1
    while 2 < l:
        rut_aux = "." + rut[l - 3:l] + rut_aux
        l = l - 3

    rut_aux = rut[0:l] + rut_aux
    l = len(rut_aux)
    rut_aux = rut_aux[l - 12:l]
    return rut_aux


def CMon(s, dec=2):
    try:
        A = float(s)
    except:
        # print dir(s)
        if isinstance(s, str):
            return None
            if not s.strip():
                return ""
        A = s
    try:
        str_format = '{:,.%sf}' % (dec)
        str_return = str_format.format(A)
        ret = [str_return.split(".")[0].replace(",", ".")]
        if dec != 0:
            ret.append(str_return.split(".")[1].replace(",", "."))
        return ",".join(ret)
    except:
        print("error", s, sys.exc_info()[1])
        return s


if __name__ == "__main__":
    db.create_all()
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, host='0.0.0.0', port=5555)
