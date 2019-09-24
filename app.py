import sys
from pivot import pivot
from reportlab.lib.styles import getSampleStyleSheet
from xbrl import XBRLParser, GAAP, GAAPSerializer
import matplotlib
import pdfkit as pdfkit
import wget as wget
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, flash, session, url_for, Response
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2 import connect
import psycopg2.extensions as _ext
from sqlalchemy.sql.functions import current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
import zipfile
import xlrd
import tempfile
import openpyxl
import string
import urllib3
import pdfkit
from datetime import datetime, timedelta

dbdir = "sqlite:///" + "xeeffy.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db_user = os.environ.get('DBAAS_USER_NAME', 'jcarrasco')
db_password = os.environ.get('DBAAS_USER_PASSWORD', '1234')
db_connect = os.environ.get('DBAAS_DEFAULT_CONNECT_DESCRIPTOR', "190.114.255.158")
service_port = port = os.environ.get('PORT', '5432')
cnx = connect(
    database='xeeffy',
    host='190.114.255.158',
    port='5432',
    user='jcarrasco',
    password='1234')

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


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(50), unique=True)
    contrasena = db.Column(db.String(50))


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if cnx.status == 1:
            username = request.form["username"]
            password = request.form["password"]
            user = Usuario.query.filter_by(usuario=username).first()
            if user and check_password_hash(user.contrasena, request.form["password"]):
                success_message = 'Bienvenido {}'.format(username)
                flash(success_message)
                session['username'] = username
                return redirect("/index")
            else:
                error_message = 'usuario o contraseña no valido'
                flash(error_message)
        else:
            flash("error al conectar bd")
            return redirect("/login")
    return render_template("/login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    session.pop("username", None)
    session["username"] = "unknown"
    return redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form["password"], method="sha256")
        new_user = Usuario(usuario=request.form["username"], contrasena=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("signup.html")


app.secret_key = "9;~X!cp4KhL9u}4#"


@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index():
    return render_template("/index.html")


@app.route('/contacts')
def contacts():
    return render_template("/contacts.html")


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


@app.route('/documentos', methods=["GET", "POST"])
def documentos():
    if session["username"] != 'unknown':
        cur = cnx.cursor()
        cur.execute("""SELECT
        public.entidad.cod_entidad,
        public.entidad.desc_entidad,
        public.documento.desc_documento,
        public.documento.anio,
        public.documento.mes,
        public.documento.cod_documento,
        public.documento.hash
        FROM
        public.documento
        INNER JOIN public.entidad ON public.documento.cod_entidad = public.entidad.cod_entidad""")
        data = cur.fetchall()
        return render_template("/documentos.html", dato=data)
    return redirect("login")


@app.route('/detalle_documento/<cod_documento>', methods=["GET", "POST"])
def detalle_documentos(cod_documento):
    if session["username"] != 'unknown':
        cur1 = cnx.cursor()
        cur = cnx.cursor()
        cur1.execute("""SELECT
public.role.cod_role,
public.role.desc_role
FROM
public.role""")
        cur.execute("""SELECT
public.detalle_documento.cod_documento,
public.cuenta.desc_cuenta
FROM
public.cuenta
INNER JOIN public.detalle_documento ON public.detalle_documento.cod_cuenta = public.cuenta.cod_cuenta
WHERE
public.detalle_documento.cod_documento ='%s'""" % cod_documento)
        data = cur.fetchall()
        data1 = cur1.fetchall()
        if data == []:
            flash("NO ENCONTRADO")
            return redirect("/documentos")
        else:
            return render_template("/detalle_documento.html", dato1=data1, dato=data, cod_documento=cod_documento)
    return redirect("login")


# @app.route('/ndocumento', methods=["GET", "POST"])
# def ndocumento():
#     if session["username"] != 'unknown':
#         if request.method == "POST":
#             entidad = request.args.get("entidad")
#             desc_documento = request.args.get("desc_documento")
#             desc_detalle_documento = request.args.get("desc_detalle_documento")
#             ano = request.args.get("ano")
#             mes = request.args.get("mes")
#             hash = request.args.get("hash")
#             cuenta = request.args.get("cuenta")
#             unidad = request.args.get("unidad")
#             decimal = request.args.get("decimal")
#             valor = request.args.get("valor")
#             contexto = request.args.get("contexto")
#             cur = cnx.cursor()
#             cur1 = cnx.cursor()
#             cur2 = cnx.cursor()
#             cur3 = cnx.cursor()
#             cur4 = cnx.cursor()
#             cur5 = cnx.cursor()
#             cur.execute("""INSERT INTO documento(desc_documento,anio,mes,hash)
#                             VALUES('%s','%s','%s','%s')""" % (desc_documento, ano, mes, hash))
#             dato = cur.fetchall()
#             cur1 = cnx.execute("""INSERT INTO entidad(desc_entidad)
#                 VALUES ('%s')""" % (entidad))
#             dato1 = cur1.fetchall()
#             cur2.execute(
#                 """INSERT INTO detalle_documento(desc_detalle_documento,decimales,valor) VALUES ('%s','%s','%s')""" % (
#                 desc_detalle_documento, decimal, valor))
#             dato2 = cur2.fetchall()
#             cur3.execute("""INSERT INTO unidad(desc_unidad) VALUES ('%s')""" % unidad)
#             dato3 = cur3.fetchall()
#             cur4.execute("""INSERT INTO contexto(desc_contexto) VALUES ('%s')""" % contexto)
#             dato4 = cur4.fetchall()
#             cur5.execute("""INSERT INTO cuenta(desc_cuenta) VALUES ('%s','%s')""" % cuenta)
#             dato5 = cur5.fetchall()
#             dato.commit()
#             dato1.commit()
#             dato2.commit()
#             dato3.commit()
#             dato4.commit()
#             dato5.commit()
#             return render_template("/ndocumento.html",dato1=dato1, dato2=dato2, dato3=dato3, dato4=dato4,
#                                    dato5=dato5)
#         cur = cnx.cursor()
#         cur.execute("SELECT desc_documento from documento")
#         dato = cur.fetchall()
#         return render_template("/ndocumento.html",dato=dato)
#     return redirect("/login")

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
    data = cursor.fetchall()
    dict = CursorPg()
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
    per = cursor.fetchall()
    for d in data:
        cod_rol = d[1]
        desc_role = d[0]
        entidad = d[13]
        cuenta = d[5]
        dineros = d[8]
        fechas = d[7]
    hoy = datetime.now()
    hoy = hoy.strftime("%Y-%m-%d")
    sql = """select desc_role, cod_role_cuenta,desc_escenario, desc_dimension, desc_tipo_cuenta,coalesce(desc_role_cuenta, etiqueta, desc_cuenta) desc_cuenta, cod_periodo,desc_periodo, desc_detalle_documento, decimales, cod_unidad, desc_unidad, cod_entidad,desc_entidad, desc_detalle_documento valor 
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
                order by cod_role_cuenta, desc_cuenta""" % (cod_documento, cod_role)
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
        columnas.append(p[0])
        data_linea.append(0.0)
        colsWidth.append(60)
        ancho_total += 60
        colAlign.append("RIGHT")
        colType.append("str")
    colsWidth[0] = 540 - ancho_total
    for f in pvt_kms:
        dl = list(f.get(('cod_role_cuenta', 'desc_cuenta'), ['']))
        for p in per:
            dl.append(f.get((p[0],), 0))
        datas.append(dl)
    data_final = []
    datas.sort()
    for d in datas:
        data_final.append(d[1:])
    report.drawData(data_final, columnas, colswidht=colsWidth, fontSize=7, ColsAlign=colAlign, ColsType=colType)
    report.go(tmp=True)
    return render_template("/pdf.html", desc_role=desc_role, entidad=entidad,
                           cuenta=cuenta,
                           dineros=dineros, fechas=fechas, hoy=hoy, data=data)
    # fileNameOutput = 'informe.pdf'
    # # css = ['/static/css/pdf.css']
    # pdfkit.from_string(cont, fileNameOutput)
    # pdfDownload = open(fileNameOutput, 'rb').read()
    # os.remove(fileNameOutput)
    # return Response(
    #     pdfDownload,
    #     mimetype="application/pdf",
    #     headers={
    #         "Content-disposition": "attachment; filename=" + fileNameOutput,
    #         "Content-type": "application/force-download"
    #     }
    # )
    # return render_template("/documentos.html")


class CursorPg:
    def dictfetchone(self, sql=None):
        if sql != None:
            try:
                self.cursor.execute(sql)
            except:
                print(str(sys.exc_info()[1]))
        r = self.cursor.dictfetchone()
        return r

    def dictfetchall(self, sql=None):
        if sql != None:
            try:
                self.cursor.execute(sql)
            except:
                print(str(sys.exc_info()[1]))
        r = self.cursor.dictfetchall()
        # aux = []
        # for i in r:
        #    daux = {}
        #    for j in i:
        #        i[j]
        return r


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
                    cur.execute(
                        """INSERT INTO documento(desc_documento,cod_entidad,anio,mes)VALUES('%s','%s','%s','%s')""" % (
                            desc_doc, CRut("%s-%s" % (rut, dv)), ano, mes))

                    url_zip = "http://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs/safec_ifrs_verarchivo.php?auth=&send=&rut=%(rut)s&mm=%(mes)s&aa=%(anio)s&archivo=%(rut)s_%(anio)s%(mes)s_%(tipo)s.zip&desc_archivo=%(archivo)s&tipo_archivo=XBRL" % (
                        filtros)
                    filename_zip = tempfile._get_default_tempdir() + os.sep + tempfile._RandomNameSequence().__next__() + "%(rut)s_%(anio)s%(mes)s_C.zip" % (
                        filtros)
                    cnx.commit()
                    #
                    # try:
                    #     data1 = urllib.request.urlretrieve(values)
                    #     req = http.request(url_zip,data1, headers)
                    #     http1 = urllib3.PoolManager()
                    #     response = http1.request(req)
                    #     the_page = response.read()
                    #     f = open(filename_zip, "wb")
                    #     f.write(the_page)
                    #     f.close()
                    #     input_zip = zipfile.ZipFile(filename_zip)
                    #     data = {name: input_zip.read(name) for name in input_zip.namelist() if
                    #             name.upper().endswith('.XBRL')}
                    # except:
                    #     print("ERROR", desc_doc, sys.exc_info()[1])
                else:
                    print("EXISTE!!!", desc_doc, rx, "de", sh.nrows)

            return redirect("/documentos")
        return render_template("/importCMF.html")
    return redirect("/login")


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


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8080)
