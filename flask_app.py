from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for, session, make_response
from flask_login import current_user, login_required, login_user, LoginManager, logout_user, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import io
from datetime import timedelta

from processing import check_first,  subkontoList, exception, korrekt_dateSwed, korrekt_dateSEB, korrekt_dateLHV, \
    first_row, mailSQL, mailText, matchSubkonto, terminalSumSwed, terminalSumSeb
import csv
import confid




app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = confid.secret_key



SQLALCHEMY_DATABASE_URI = confid.SQLALCHEMY_DATABASE_URI

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = confid.app_secret_key
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()




@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)




@app.route("/", methods=["GET", "POST"])

def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    user = load_user(request.form["username"])
    if user is None:
        return render_template("login_page.html", error=True)

    if not user.check_password(request.form["password"]):
        return render_template("login_page.html", error=True)

    login_user(user)
    return redirect(url_for('file_summer_page'))





@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




class LOGS(db.Model):

    __tablename__ = "LOGS"

    log_id = db.Column(db.Integer, primary_key=True)
    log_user = db.Column(db.String(40))
    log_aa = db.Column(db.String(20))
    log_stat = db.Column(db.String(20))
    log_time = db.Column(db.DateTime, default=datetime.now)


class AA(db.Model):

    __tablename__ = "AA"
    aa_id = db.Column(db.Integer, primary_key=True)
    aa_aa = db.Column(db.String(40))
    aa_ow = db.Column(db.String(40))




@app.route("/statement/", methods=["GET", "POST"])
@login_required
def file_summer_page():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    else:
        if request.method == "POST":

            #загрузка файлов
            input_file = request.files["input_first"]
            sbkonto_f = request.files["input_subkonto"]
            noaccount_f = request.files["input_except"]
            statement_f = request.files["input_statement"]

            #обработка файла first
            first = input_file.read().decode('UTF-8')
            variableDict = check_first(first)

            #обработка файла subkonto
            try:
                IgaSubkonto = variableDict['IgaSubkonto']
                viivis = variableDict['viivis']
                terminal = variableDict['terminal']
                termList = str(variableDict['term_nr']).split(' --/-- ')
            except:
                IgaSubkonto = "0"
                viivis = "0"
                terminal = "0"
                termList = ""
            sbkonto = io.StringIO(sbkonto_f.stream.read().decode("latin-1"), newline=None)
            subkonto = subkontoList(sbkonto, IgaSubkonto)


            #обработка файла исключений
            noaccount = io.StringIO(noaccount_f.stream.read().decode("latin-1"), newline=None)
            subexept = exception(noaccount)


            #загрузка основной обработки
            #обработка банковской выписки
            csv_file = io.StringIO(statement_f.stream.read().decode("latin-1"), newline=None)

            output_data1 = ''
            error_part = ''
            err_first = ''
            all_dates = []



            valjavotte = variableDict['PankStatement']
            if valjavotte == 'SEB':
                col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col0', 'kood', 'tuup', 'summa', 'viite',
                'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
                readerS = csv.DictReader(csv_file, delimiter=';', fieldnames=col_names)
            elif valjavotte in ('SWED', 'SWEDCR'):
                col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi', 'col1', 'col0', 'tuup', 'summa', 'viite',
                'arhiiv', 'selgitus', 'col', 'valuuta', 'col2']
                readerS = csv.DictReader(csv_file, delimiter=';', fieldnames=col_names)
                next(readerS)  # пропускаем первую строку с заголовками
            elif valjavotte == 'LHV':
                col_names = ['meie', 'nr', 'kuupaev', 'aa', 'nimi','col1', 'col0', 'tuup', 'summa', 'viite',
                'arhiiv', 'selgitus', 'col', 'valuuta', 'col2', 'col3', 'col4', 'col5', 'col6']
                readerS = csv.DictReader(csv_file, delimiter=',', fieldnames=col_names)
                next(readerS)  # пропускаем первую строку с заголовками


            for row in readerS:
                if valjavotte == 'SWED':
                    row['kuupaev'] = korrekt_dateSwed(row['kuupaev'])
                elif valjavotte == 'SEB':
                    row['kuupaev'] = korrekt_dateSEB(row['kuupaev'])
                elif valjavotte == 'LHV':
                    row['kuupaev'] = korrekt_dateLHV(row['kuupaev'])
                elif valjavotte == 'SWEDCR':
                    row['kuupaev'] =str(row['selgitus']).split(' ')[1]
                    selg=str(row['selgitus']).strip(' ').split(' ')[2:]
                    row['selgitus'] = ''.join(selg).strip()
                log_aa = row['meie']
                # подтягиваем значения из шестерки
                sk = ''
                shet = ''
                subshet = ''
                SumViivis = ''
                err_flagCh = '1'
                tv = ''
                selg = row['selgitus'].split(';')
                SumTerm = ''
                tterm = ''


                # прокручиваем список исключений без расчетных счетов
                for exeption in subexept:
                    a = exeption['field']
                    if exeption[' value'] in row[a]:
                        sk = exeption[' subkonto']
                        shet = exeption[' konto']
                        subshet = exeption[' subk']
                        err_flagCh = '0'



                if row['aa'] in subkonto:
                    FindSum=0
                    if IgaSubkonto == "1":  #если нужно закрывать каждый счет отдельно
                        if len(subkonto.get(row['aa'])) > 1:
                            i = 0
                            countArve = len(subkonto.get(row['aa']))-1
                            while i <= countArve: #ищем совпадающую сумму в субконто
                                if subkonto.get(row['aa'])[i][2] == str(row['summa']).replace(',', '.'):
                                    sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row, i)
                                    sumSub = subkonto.get(row['aa'])[i][2]
                                    FindSum = 1
                                i += 1

                            else: #если суммы нет - закрывается все на первый субконто
                                if FindSum == 0:
                                    sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)

                        else: #если только одна сумма у субконто - закрывается все на первый субконто
                            sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
                    else:  #если закрываем суммарно субконто + закрываем пени у квартир
                        sk, shet, subshet, err_flagCh = matchSubkonto(subkonto, row)
                        sumSub = subkonto.get(row['aa'])[0][2]







                if row['tuup'] == 'C':
                    if viivis == '1' and sumSub !='':  #если нужно закрывать пени у квартир и есть сумма в субконто
                        row_summa = float(str(row['summa']).replace(',', '.'))
                        if float(sumSub)>=row_summa: #если пени больше перевода
                            SumViivis = str(format(row_summa, '.2f'))
                            SumAtS = str("0.00")
                            subkonto.get(row['aa'])[0][2] = float(sumSub)-row_summa
                        else:
                            SumViivis = str(format(float(sumSub),'.2f')) #если пени меньше перевода
                            SumAtS=str(format(row_summa-float(SumViivis), '.2f'))
                            subkonto.get(row['aa'])[0][2] = "0.00"
                    else:
                        SumAtS = str(row['summa']).replace(',', '.')

                    if terminal == '1':  #перебираем терминалы аtermListиз установочного файла
                        for term_item in termList:
                            if term_item in row['selgitus']: #вытаскиваем сумму реализации и расхода из пояснения
                                if valjavotte == 'SWED':
                                    SumAtS, SumTerm = terminalSumSwed(selg)
                                elif valjavotte == 'SEB':
                                    SumAtS, SumTerm = terminalSumSeb(selg, row['summa'])
                    DShet = '"' + variableDict['ShetPank'] + '"'
                    DSubShet = '"' + variableDict['SubShetPank'] + '"'
                    KShet = '"' + shet + '"'
                    KSubShet = '"' + subshet + '"'
                    DSubkonto = variableDict['Subkonto']
                    KSubkonto = sk
                else:
                    if valjavotte in ('SWED', 'LHV', 'SWEDCR'): #убираем знак минус из выписки
                        SumAtS = str(row['summa']).replace(',', '.')[1:] #сумма в строке, если без пени
                    elif valjavotte == 'SEB':
                        SumAtS = str(row['summa']).replace(',', '.')
                    KShet = '"' +variableDict['ShetPank']+'"'
                    KSubShet = '"' +variableDict['SubShetPank']+'"'
                    KSubkonto = variableDict['Subkonto']
                    DSubkonto = sk
                    DShet = '"' + shet + '"'
                    DSubShet = '"' + subshet + '"'



                # собираем строку в файл вывода
                tt = '"' +variableDict['zhurnal']+'"' + ',' + \
                     '"' + row['kuupaev'] + '",' + \
                     DShet + ','+ \
                     DSubShet + ',' + \
                     KShet + ',' + \
                     KSubShet + ',' + \
                     '"' + SumAtS + '",' + \
                     '"' + row['selgitus'] + ' ' + row['nimi'] + '",' + \
                     '"' + DSubkonto + '",' + \
                     '"' + KSubkonto + '",' + \
                     '"","",""'+'\r\n'
                #собираем все даты для первой строки, чтобы найти начало и конец
                all_dates.append(row['kuupaev'])

                if SumViivis != '':  #собираем строку пени
                    KShet = '"62"'
                    KSubShet = '"4"'
                    tv = '"' +variableDict['zhurnal']+'"' + ',' + \
                        '"' + row['kuupaev'] + '",' + \
                        DShet + ',' + \
                        DSubShet + ',' + \
                        KShet + ',' + \
                        KSubShet + ',' + \
                        '"' + SumViivis + '",' + \
                        '"' + 'VI ' + row['selgitus'] + ' ' + row['nimi'] + '",'+ \
                        '"' + DSubkonto + '",' + \
                        '"' + KSubkonto + '",' + \
                        '"","",""'+'\r\n'

                if SumTerm !='': #собираем строку услуг за терминал за сделку
                    DShet =variableDict['kulud'].split(',')[0].strip('"')
                    DSubShet = variableDict['kulud'].split(',')[1]
                    DSubkonto =variableDict['kulud'].split(',')[2].strip('"')
                    KShet = '"' + variableDict['ShetPank'] +'"'
                    KSubShet = '"' + variableDict['SubShetPank']+'"'
                    KSubkonto = variableDict['Subkonto']
                    tterm = '"' +variableDict['zhurnal']+'"' + ',' + \
                        '"' + row['kuupaev'] + '",' + \
                        '"' +DShet + '",' + \
                        DSubShet + ',' + \
                        KShet + ',' + \
                        KSubShet + ',' + \
                        '"' + SumTerm + '",' + \
                        '"' + row['selgitus'] + '",' + \
                        '"' + DSubkonto + '",' + \
                        '"' + KSubkonto + '",' + \
                        '"","",""'+'\r\n'


                output_data1 = output_data1+ tt + tv + tterm

                if err_flagCh == '1':  #собираем вывод ошибок
                    err_first = '\n\n\n' + '---ERROR PART---'+'\n'
                    err_tt = '--ERROR--' + tt+row['aa']+'\n'
                    error_part = error_part + err_tt

            first_rowOut = first_row(all_dates) + '"' + variableDict['zhurnal']+'"'+ '\r\n'

            output_data = str(first_rowOut) + output_data1+err_first + error_part

            response = make_response(output_data)
            response.headers["Content-Disposition"] = "attachment; filename=result.txt"

            log_row = LOGS(log_user=current_user.username, log_aa=log_aa, log_stat=valjavotte)
            db.session.add(log_row)
            db.session.commit()

            formail = db.session.query(LOGS.log_user, LOGS.log_time, AA.aa_ow, LOGS.log_aa).join(AA,
                            LOGS.log_aa == AA.aa_aa).order_by(db.desc(LOGS.log_id)).limit(1).all()
            mailSQL(mailText(formail))
            return response

        return render_template("statement.html", error=True)
